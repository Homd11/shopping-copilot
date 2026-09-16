import os
import shutil
import subprocess
import sys
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]


def _pnpm_command() -> str:
    command = shutil.which("pnpm")
    if command is None:
        raise RuntimeError("pnpm is required to run the local browser evaluation")
    return command


def service_commands(node: Path) -> tuple[list[str], ...]:
    return (
        [
            sys.executable,
            "-m",
            "uvicorn",
            "agent.app:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8000",
        ],
        [
            str(node),
            str(ROOT / "store" / "node_modules" / "tsx" / "dist" / "cli.mjs"),
            str(ROOT / "store" / "src" / "server.ts"),
        ],
        [
            str(node),
            str(ROOT / "panel" / "node_modules" / "vite" / "bin" / "vite.js"),
            str(ROOT / "panel"),
            "--host",
            "0.0.0.0",
            "--port",
            "4100",
        ],
    )


def _wait_for(url: str, timeout_seconds: float = 20) -> None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        try:
            with urlopen(url, timeout=1) as response:  # noqa: S310 - fixed local evaluation URLs
                if response.status < 500:
                    return
        except (URLError, TimeoutError):
            time.sleep(0.1)
    raise RuntimeError(f"Local service did not become ready: {url}")


@contextmanager
def local_services() -> Iterator[None]:
    pnpm = _pnpm_command()
    node = shutil.which("node")
    if node is None:
        raise RuntimeError("Node.js is required to run the local browser evaluation")
    subprocess.run(  # noqa: S603 - fixed local command without a shell
        [pnpm, "--filter", "@shopping-copilot/bridge", "build"],
        cwd=ROOT,
        check=True,
    )
    creation_flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    commands = service_commands(Path(node))
    processes = [
        subprocess.Popen(  # noqa: S603 - fixed local commands without a shell
            command,
            cwd=ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creation_flags,
        )
        for command in commands
    ]
    try:
        _wait_for("http://127.0.0.1:8000/health")
        _wait_for("http://127.0.0.1:4000/")
        _wait_for("http://127.0.0.1:4100/")
        yield
    finally:
        for process in processes:
            process.terminate()
        for process in processes:
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
