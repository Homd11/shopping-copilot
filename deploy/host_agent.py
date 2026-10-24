"""Explicit single-process host entry; no import-time server or provider activation."""

import argparse
import asyncio
import sys
from pathlib import Path

from uvicorn import Config, Server

from deploy.host_bootstrap import create_host_app
from deploy.host_config import load_host_settings


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise ValueError("Host startup refused")


async def _serve(app):
    try:
        # Uvicorn can log a lifespan traceback before returning without starting.
        # Limit suppression to its own loggers; CLI errors remain fixed and redacted.
        quiet = {"handlers": ["null"], "propagate": False}
        config = Config(
            app,
            host="127.0.0.1",
            port=8000,
            workers=1,
            reload=False,
            lifespan="on",
            proxy_headers=False,
            access_log=False,
            server_header=False,
            log_config={
                "version": 1,
                "disable_existing_loggers": False,
                "handlers": {"null": {"class": "logging.NullHandler"}},
                "loggers": {
                    name: dict(quiet) for name in ("uvicorn", "uvicorn.error", "uvicorn.access")
                },
            },
        )
        server = Server(config)
        await server.serve()
        if not server.started:
            raise RuntimeError("Host startup refused")
    finally:
        await app.state.host_cleanup()


def main(argv=None):
    try:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            pass
        else:
            raise ValueError()
        parser = _Parser(description="Run the restricted host Agent", allow_abbrev=False)
        parser.add_argument("--config", type=Path, required=True)
        args = parser.parse_args(argv)
        settings = load_host_settings(args.config)
        app = create_host_app(settings)
        asyncio.run(_serve(app))
        return 0
    except KeyboardInterrupt:
        code = 130
    except (Exception, SystemExit) as error:
        if isinstance(error, SystemExit) and error.code == 0:
            return 0
        code = 1
    print("Host startup refused", file=sys.stderr)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
