"""Evaluation-only Agent entrypoint; never enabled by normal app startup."""

import os
from dataclasses import replace
from pathlib import Path
from uuid import uuid4

from agent.app import create_app
from agent.llm import build_llm_client, load_llm_settings
from eval.measurement import MeasuredClient

if os.environ.get("MILESTONE_EVAL") != "1":
    raise RuntimeError("This entrypoint is only for explicit local milestone evaluation")
settings = replace(load_llm_settings(), stream=True)
client = MeasuredClient(
    build_llm_client(settings),
    journal=Path("eval/reports") / f"attempts-{uuid4()}.jsonl",
)
app = create_app(llm_settings=settings, llm_client=client)


@app.get("/__eval/metrics")
def metrics():
    return {
        "provider": settings.provider,
        "model": settings.model,
        "calls": client.calls,
        "journal": client.journal.as_posix(),
    }


@app.post("/__eval/hold")
async def hold():
    client.release.clear()
    return {"held": True}


@app.post("/__eval/release")
async def release():
    client.release.set()
    return {"held": False}
