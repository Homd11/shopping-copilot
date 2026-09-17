from pathlib import Path

from eval.services import ROOT, service_commands, service_environment


def test_node_services_are_launched_as_owned_processes() -> None:
    commands = service_commands(Path("node"))

    assert commands[1][0] == "node"
    assert Path(commands[1][1]).as_posix().endswith("store/node_modules/tsx/dist/cli.mjs")
    assert commands[2][0] == "node"
    assert Path(commands[2][1]).as_posix().endswith("panel/node_modules/vite/bin/vite.js")
    assert commands[2][2] == str(ROOT / "panel")


def test_local_evaluation_explicitly_selects_the_scripted_model() -> None:
    environment = service_environment({"PATH": "test-path"})

    assert environment["PATH"] == "test-path"
    assert environment["LLM_PROVIDER"] == "scripted"
    assert environment["LLM_MODEL"] == "scripted-v1"
