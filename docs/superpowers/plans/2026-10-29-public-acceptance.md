# Public Acceptance Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Enforce the approved four-attempt live allowance and execute the consolidated public acceptance safely.

**Architecture:** Reuse the ledger's atomic absolute attempt ceiling. Carry an optional operator-pinned integer from the root-owned systemd command through the existing host/app factories to GuardedClient, without changing model configuration or recalculating the ceiling on restart. Reuse existing access, packaging, observation and private-host operator seams for bounded cloud execution.

**Tech Stack:** Python3.12, pytest, SQLite, existing AL2023/systemd/Caddy, AWS CLI and existing AWS SDK adapters.

**Spec:** `docs/cap-public-acceptance-proposal-20261029.md`, owner-approved29October.

## Global constraints

- AWS USD2 existing credits, Free/USD0cash, four hours; only disabled-edge cleanup tail24hours.
- Existing host at most2starts, one temporary EIP; no new host/root/table/profile.
- At most4 live POSTs/USD0.10 inside unchanged nonresetUSD2; readiness reserve preserved; at most5 key-status GETs.
- Preserve custody/history, generation3 authority, sensitive-field exclusion, bound Confirmation, stale/duplicate refusal and refresh uncertainty.
- Keep startup-only hashing; no per-request file rehashing or runtime source-byte pinning.

## Review focus

- Concurrent and restarted callers share an absolute ceiling, not four fresh slots each.
- Invalid limits fail closed before a provider request; missing optional limit preserves existing behavior.
- A changed in-memory ceiling invalidates captured qualification.
- The host CLI persists the operator's fixed number and requires qualified custody for capped operation.
- Partial cloud success preserves ownership receipts and never starts the four-hour clock during local preparation.

## Task1 — Atomic GuardedClient attempt ceiling

Files: `agent/inference/client.py`, `agent/inference/config.py`, `agent/tests/test_inference_runtime.py`.

- [x] RED: add real-ledger tests for historical attempts plus four concurrent attempts, fifth refusal before provider entry, and reconstruction with the same pinned ceiling; validate invalid types and unconfigured-guard bypass.
- [x] Implement optional `maximum_attempts=None` on GuardedClient/configured_guard and pass it unchanged to ledger.reserve in the existing transaction/thread seam. No retry/refund or ledger reset.
- [x] Run focused inference tests and confirm GREEN.

## Task2 — Qualified host wiring

Files: `agent/app.py`, `deploy/host_bootstrap.py`, `deploy/host_agent.py`, `deploy/provider_qualification.py`; tests in `eval/tests/test_host_agent.py`, `eval/tests/test_provider_qualification.py` and host integration tests.

- [x] RED: pin host CLI/factory propagation, malformed limit refusal and qualification refusal after in-memory limit mutation.
- [x] Add explicit trusted factory arguments and `--maximum-attempts`; require the existing qualification flags when the CLI limit is supplied. Never read a browser value or calculate count+4 at boot.
- [x] Capture the limit in ProviderQualification's in-memory signature.
- [x] Run affected host/provider/inference checks and lint/format:88 focused tests pass; full regression1617passed/2existing warnings, exit0.
- [x] Rebuild native release and affected Lambda ZIPs before cloud use: clean source44e4952, native release and both isolated Linux Lambda smoke checks passed. See docs/public-preparation-pause-20261029.md for proof limits.

Ruling: use the root-owned unit's literal absolute ceiling rather than another runtime configuration schema/file. This is an operator setting, not a secret. Record the baseline and ceiling once in the protected operation; install the same literal for both starts/restarts. HostSettings/model configuration fingerprint remains unchanged. The approved local code change necessarily creates a new immutable release; bind its independently verified release fingerprint while retaining the same accepted qualification report, model configuration, key and ledger. Never patch an old release or claim its old digest covers new bytes.

## Task3 — Protected bounded operator and approved cloud session

Files: protected `.scratch/cap08-public-preparation/` operator and synthetic tests; public sanitized evidence/results/checkpoint only.

- [x] Recover exact existing resources and receipts; record the actual approval/proposal digest and new artifacts without moving live secrets to the PC.
- [ ] Prepare/test write allowlists, partial-create reconciliation, start/EIP/request ceilings, DNS baseline/TTL checks and independent deadline cleanup. Refresh official prices and Free eligibility; bind generated identifiers only after receipt.
- [ ] Run the approved ordered gates from the spec: disabled/private control provisioning, inspect-first maintenance, public TLS/OAC, genuine invitation cold wake, desktop/Android checks, real idle shutdown and teardown. No extra approval round within the approved exact bounds.
- [ ] Retrieve diagnostics before shutdown, preserve canonical accounting, independently verify all new resources deleted and original host stopped/no EIP, then publish evidence and final limitations.

Execution ledger: owner subsequently said “lets finish this project,” then explicitly paused for usage limits and requested a checkpoint, intending to return in about three hours. Resume only on owner input. See `docs/public-preparation-pause-20261029.md`. No Computer Use or Brave access; DNS edits remain owner-only. Native and Lambda artifacts are rebuilt, but Task3/operator, deadline worker, partial-create failure coverage and deployed acceptance remain incomplete. No cloud mutation/session clock has begun; host stopped, no EIP, no provider/model calls. Docker is stopped. No automatic resumption was scheduled.

30October continuation: see docs/public-operator-preparation-20261030.md.55operator/84integration checks pass; three independent-review findings fixed; final joined driver rehearsal remains before cloud. Owner reports21% quota; launch held, no clock/resources/model calls. Existing scope unchanged; no duplicate approval merely for hold.
