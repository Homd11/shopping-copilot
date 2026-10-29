# CLAUDE.md — Shopping Copilot

## Project Overview

Arabic-first shopping assistant turning Egyptian Arabic, English, Franco-Arabic, and mixed-language requests into visible, controlled browser actions.

## Monorepo Architecture

- `agent/`: Python 3.12 / FastAPI service handling task execution, intent validation, planning, sessions, confirmation, and LLM provider adapters.
- `bridge/`: TypeScript browser bridge for semantic page observation, action execution, and client-side safety checks.
- `panel/`: TypeScript / Vite chat interface (port 4100) managing task status, shopper decisions, and recovery coordination.
- `store/`: Node / Express controlled storefront (port 4000) backed by a local SQLite catalogue, managing cart state, 10-second Undo, and fictional checkout.
- `eval/`: Python / Playwright browser regression and evaluation suite.
- `protocol/v1/`: Shared fixtures for versioned Snapshot, Action, and Action Result contracts.

## Toolchain & Local Services

- **Runtime versions**: Python 3.12 (`.venv`), Node.js 24.13.0, and `pnpm` 11.19.0.
- **Start Storefront & Bridge**: `pnpm run store` (runs on `http://localhost:4000`).
- **Start Agent**: `python -m uvicorn agent.app:app --host 127.0.0.1 --port 8000` (health check at `/health`).
- **Start Panel**: `pnpm run panel` (runs on `http://localhost:4100`).

## Verification & Quality Gates

Always run verification checks before concluding any task (stop running demo services on ports 4000, 4100, and 8000 before running browser suites):

- **Full CI suite (521+ Python & TypeScript tests)**: `make ci` (or `pnpm format:check && pnpm lint && pnpm test && pnpm build`).
- **Browser evaluation runner**: `pnpm eval:browser`.

## Safety & Architectural Invariants (Strict)

- **Intent vs. Execution**: The LLM only interprets intent from a sanitized Snapshot; deterministic code validates, executes, and verifies browser actions.
- **Browser Boundaries**: The Bridge blocks off-origin navigation, excludes sensitive fields from snapshots, and treats storefront text strictly as untrusted data.
- **Guarded Actions**: Bulk cart clearing and checkout require a single-use bound confirmation (expires after 60s, state change, or refresh).
- **State & Secrets**: Never commit `.env`, `.scratch/`, or `work/` (`work/local-identity.json` and SQLite runtime files). Respect `OPENROUTER_TOTAL_CAP_DOLLARS` limits.

## Active Engineering Roadmap

- **Ticket 14**: Implement SPA navigation, controlled inputs, and event-stream reconnection under the existing safety contract.
- **Ticket 15**: Execute and verify the 44-case evaluation gate (minimum 40/44 passing across 3 runs, 100% safety pass rate).
- **Architecture Refactoring (`agent/sessions.py`)**: Incrementally decouple session lookup/tab ownership, task transitions, and intent/planning into a clean Shopping Task execution module while preserving wire contracts and passing all regression tests.
