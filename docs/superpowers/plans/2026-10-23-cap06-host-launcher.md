# Host Agent launcher implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Prepare an explicit inactive host Agent launch path with owned cleanup.

**Architecture:** Build the protected host app before entering asyncio, serve it
with fixed Uvicorn settings, and drain owned resources on that same loop even
when startup never enters lifespan. Package a separate inactive Agent unit.

**Tech Stack:** Existing Python 3.12, FastAPI, Uvicorn 0.35, pytest, systemd template.

**Spec:** `docs/superpowers/specs/2026-10-23-cap06-host-launcher-design.md`.

## Global constraints

- Loopback 127.0.0.1:8000, one process, lifespan on; no provider qualification switch.
- No AWS/model/credential calls, deployment, unit installation/activation or spend.
- Keep combined runtime unchanged; no Action replay or safety gate waiver.
- Fixed redacted failure; cleanup before returning, SDK closed exactly once.

## Review focus

- An already-running loop must refuse before reading protected inputs.
- Early server failure must release resources even without a lifespan context.
- Cancellation and normal lifespan cleanup must not double-close the shared SDK.
- Internal Uvicorn logging must not reveal an exception that the CLI redacts.
- A packaged release must contain the actual launcher and separate inactive unit.

## Task 1: Explicit launch path and inactive unit

**Files:** create `deploy/host_agent.py`,
`deploy/shopping-copilot-agent.service`, `eval/tests/test_host_agent.py` and
`docs/cap06-host-launcher.md`; modify `deploy/host_bootstrap.py`,
`deploy/artifact.py` and the existing release-build test.

**Interfaces:** consume `load_host_settings(path)` and `create_host_app(settings)`;
produce app.state.host_cleanup async callback, `host_agent.main(argv=None)` integer
status, and private `_serve(app)` coroutine for same-loop cleanup. Tests inject
dependencies by monkeypatch, never through CLI/environment options.

- [x] Write `test_preloop_assembly_and_fixed_server`,
      `test_running_loop_refuses_before_loading`,
      `test_failure_is_redacted`, `test_server_never_started_is_failure`,
      `test_cleanup_without_lifespan`, `test_cleanup_after_lifespan`,
      `test_cancelled_server_drains_resources`, `test_closed_provider_stays_closed`,
      `test_unknown_switch_cannot_bypass_gate`, `test_prepared_unit_and_release`.
      Assert exact call ordering/settings/status/redacted text, close-once SDK and
      no model calls/ledger change. Exercise the real factory with synthetic fixtures
      for cleanup/readiness, rather than mocking resource ownership.
- [x] Run project Python `-m pytest eval/tests/test_host_agent.py -q`; expect
      missing launcher failures before implementation.
- [x] Move existing factory cleanup into a reusable closure and attach it to the
      successful app. Implement `_serve` with `try/finally` enclosing config/server
      creation and `await server.serve()`, then await owned cleanup. `main` rejects a
      running loop, loads and constructs synchronously, catches errors generically
      and returns nonzero for interruption or server that never started.
- [x] Prepare the separate unit from the existing hardened template, using
      `-m deploy.host_agent --config /etc/shopping-copilot/host.json`. Add its path to
      the release allowlist; keep the legacy unit unchanged. Update the actual fresh
      release-build assertion. Write the operator guide describing uninstalled state,
      port conflict, closed model gate and remaining full host acceptance.
- [x] Run focused launcher/bootstrap/config/checks/release tests, then all-Agent,
      host/control/browser/runtime regression and fresh release-build tests. Expected:
      all pass, no safety regressions; no model requests or external SDK activation.
- [x] Run Ruff check/format on agent/eval/deploy, pip check, TypeScript lint,
      changed Markdown/JSON Prettier, and git diff --check. Expected: pass.
- [x] Record exact AL2023 image/artifact/test evidence and Docker recovery/update,
      update checkpoint and guide limitations. Fresh reviewer checks this complete
      change against spec, including the five review-focus conditions.
- [x] Commit explicit changed files locally after checks and review. No push.
