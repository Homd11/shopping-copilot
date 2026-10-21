# CAP-06 command executor and startup HTTP implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Prepare a single-dispatch executor and bounded waiting endpoint offline.

**Architecture:** Inject the existing DynamoDB lifecycle, EC2 client and durable
three-lane rate store. Keep command execution separate from HTTP. No runtime
factory selection or deployment.

**Tech Stack:** Python, existing boto3/botocore, optional Moto, pytest.

**Spec:** docs/superpowers/specs/2026-10-22-cap06-command-startup.md.

## Global constraints

- Stockholm only; no SDK retries, client/credential creation or real AWS/model calls.
- Exact fixed instance; one exclusive claim and at most one command per execution.
- Uncertain calls/settlement remain locked; no automatic replay or takeover.
- Existing runtime provider, safety invariants and Free plan remain unchanged.
- No deployment, DNS, certificate request, infrastructure write or push.

## Review focus

- Reopening/competing executors must not redispatch a claimed intent (Task 1).
- Lost success or malformed SDK acknowledgement cannot become ready (Task 1).
- Revocation, deadline and mutated client configuration before SDK entry (Task 1).
- Rate rollback, corruption and concurrent increments fail closed (Task 2).
- Transport/header/JSON ambiguity cannot expose codes or initiate commands (Task 2).

## Task 1: single command executor

Files: add agent/lifecycle/executor.py and agent/tests/test_lifecycle_executor.py;
modify agent/lifecycle/dynamodb.py to expose check_command(receipt).

Interfaces: EC2CommandExecutor(lifecycle, client, instance_id).execute_once()
returns None when no command, otherwise acknowledged/uncertain; raises fixed
LifecycleUnavailable for unsafe configuration or uncertain settlement.

- [x] Write failures for the review-focus cases, single start/stop, fixed target,
      strict client/response validation and acknowledgement without readiness.
- [x] Run the focused pytest file and retain RED evidence.
- [x] Implement bounded configuration, refreshed claim check, single SDK entry,
      response validation and one settlement attempt.
- [x] Run focused executor and remote lifecycle tests; inspect every failure.

## Task 2: durable rates and startup endpoint

Files: add agent/lifecycle/startup.py and agent/tests/test_startup.py. Reuse the
existing waiting.html without changing local HTTP behavior.

Interfaces: DynamoStartupRates(invitations, clock=...).rate(lane), lanes
http/wake/poll; create_startup_handler(lifecycle, rates, origin=...) -> handler.
Handler consumes HTTP-v2 events and returns statusCode/headers/body objects.

- [x] Write failing durable rate persistence/concurrency/corruption tests and
      event transport/origin/body/JSON/CSP/privacy/routing tests.
- [x] Run the focused file and retain RED evidence.
- [x] Implement fixed conditioned rate rows and bounded pure handler.
- [x] Run endpoint, invitation, lifecycle and executor tests to GREEN.

## Task 3: verify, review and record

Files: extend eval/tests/test_release.py packaging assertions; update lifecycle
guide, PROJECT_CHECKPOINT.md and handoff.md; add dated evidence JSON.

- [x] Confirm both new modules appear in a fresh release artifact.
- [x] Run relevant regression suite, release build, repository lint/format,
      pip check and git diff --check; inspect outputs.
- [x] Dispatch one fresh-context independent review of the whole slice, resolve
      findings with failing regressions and rerun affected checks.
- [x] Record exact evidence/limits, update checkpoint/handoff and commit locally.

## Execution ledger

Ruling: continue inline under the owner's repeated go/continue instructions and
already selected topology; routine bounded interface choices are builder calls.
No new service or resource is authorized. A separate deployment approval is still
required. Existing isolated worktree is reused; original checkout is untouched.

Self-review: all spec behaviors map to Tasks 1–3; no missing interfaces or new
dependencies. Offline implementation cannot establish AWS IAM, cost or TLS.

Builder check: fresh agent found nothing important left. Pre-flight: Task 1 uses
the existing exclusive claim/completion protocol; Task 2 consumes only wake/status
and invitation validation, never the executor. Task 3 packages both modules. No
shared interface conflict. Existing native Windows workflow records task briefs,
RED/GREEN results and rulings here without POSIX-only task wrapper scripts.

Ruling: fixed rate lanes also write permanent metadata markers on first use.
Deleting a lane row cannot reinitialize its allowance. This costs one metadata
update in the first transaction per lane and no additional rows beyond three.

Task 1 RED: executor module missing. Initial GREEN:62 executor/lifecycle cases.
Task 2 RED: startup module missing. Initial implementation exposed invalid-code
status mapping and a test body override error. Corrected exact invitation
prevalidation/503 authority failures and the test input construction.

Ruling: Moto's transaction backup/rollback implementation lacks thread isolation.
The concurrency harness serializes only simulated server transactions, while
concurrent strong reads and CAS still race. No production lock was added and no
real AWS concurrency qualification is claimed. Fixed core:112passed/no skips.

Fresh independent review and inline inspection reproduced two dispatch timing
gaps. Added RED tests for invitation I/O crossing the start deadline and client
policy mutation during authority I/O. Final deadline check now follows invitation
I/O; final EC2 policy check follows authority I/O. Both claims stay locked when a
guard refuses. No EC2 operation is attempted in those regressions.

Task 1: complete. Task 2: complete. Task 3: complete. Final independent review
clear after both timing fixes;114core checks independently passed in49.51s.
Final admission/lifecycle/allowance suite and fresh release build:211passed,
zero failures/skips in82.78s. ESLint/Prettier, Ruff check/format216files, pip check
and git diff --check pass. Existing backend/provider/base locks and loopback
rehearsal are unchanged. No real AWS/EC2/model calls or resource/DNS/TLS writes.
Commit locally without push; deployment readiness and all open gates stay open.
