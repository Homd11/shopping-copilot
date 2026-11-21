import pytest


@pytest.fixture(autouse=True)
def isolated_agent_state_file(tmp_path, monkeypatch):
    """Ordinary tests never share (or write to) the default `work/` session file."""
    monkeypatch.setattr("agent.state_store.default_state_path", lambda: tmp_path / "agent-state.db")
