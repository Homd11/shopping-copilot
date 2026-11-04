# December invitation-only operation implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Run the accepted Controlled Storefront for invited testers through the approved December closing date, with bounded spending and independent cloud stop.

**Architecture:** Extend the existing DynamoDB invitation/lifecycle authority with an explicitly bound finite operating record. Reuse the current host, qualified provider and control stack; add one private guard and a direct scheduled EC2 stop. Preserve the canonical allowance and all uncertain holds.

**Tech Stack:** Python 3.12, existing boto3/httpx, DynamoDB transactional writes, Lambda, IAM/Scheduler, Caddy/systemd, existing TypeScript Storefront/Panel; no additional runtime dependency.

**Spec:** ../specs/2026-11-04-invitation-only-december-operating-design.md (approved by owner on 4 November 2026).

## Global Constraints

- Close 4 December 2026, 23:59 Cairo / 21:59 UTC; no rolling expiry.
- USD45 existing AWS credits; Free/USD0 cash; at least USD65 remaining before first write, USD35 observed-reduction / USD30 balance trip points.
- One original t3.small Standard / encrypted 20-GiB gp3; one EIP, at most 100 lifetime start dispatch reservations and eight-hour uninterrupted run threshold.
- Three functions / four roles / three schedules / one distribution / two OACs / one origin-request policy / one bucket / three logs / two actionless alarms. No replacement EC2, upgrade, provisioned concurrency, paid DNS or Virginia ACM.
- At most ten invitations, two browser redemptions / 100 created sessions each; no more than eight simultaneous shopping sessions.
- USD0.20 / 100 additional OpenRouter attempts, including two launch-smoke requests, original nonreset USD2 cap; preserve USD0.10 unexposed reserve and twenty uncertain holds. At most 100 adapter key GETs plus ten operator GETs.
- Existing ownership, Sensitive Field, Confirmation, stale/duplicate and refresh rules are mandatory regressions. Protected evidence hashing stays startup-only.
- DNS TTL 7,200 seconds starts only after authoritative proof. Cleanup tail maximum 48 hours; no unsafe IP release if DNS remains referenced.
- Owner explicitly approved implementation/deployment and asked autonomous execution while away. Use native execution; no additional plan-confirmation loop. Stop only for a material out-of-scope decision or unavoidable authentication/security challenge.

## Review Focus

1. A missing/deleted operating marker, stale config or malformed authority must not silently select legacy/unbounded operation (Tasks 1/2).
2. A concurrent/lost start reservation must be counted without dispatch replay, including maintenance and process restarts (Tasks 1/2/4).
3. An already-warm Lambda/host crossing expiry, or an unavailable DynamoDB table, must not keep admitting work; independent stopping must still run (Tasks 2/3).
4. A rebooted/unavailable PC, delayed IAM/CF APIs or partial cleanup must not be reported as successful shutdown/deletion (Tasks 3/4/5).
5. Live allowance changes and uncertain settlements must preserve prior accounting plus an inaccessible readiness reserve across stop/start (Tasks 4/5).

---

### Task 1: Finite authority and durable start reservations

**Files:** Create `agent/lifecycle/operating.py`, `agent/tests/test_operating.py`; modify `agent/admission/dynamodb.py`.

**Interfaces:** `OperatingPolicy(operation, manifest_sha256, instance, opens, closes)` validates immutable finite identity/time. `OperatingAuthority(store, policy)` exposes `initialize`, `check`, `reserve_start(command_id)`, `close(reason)`, and `status` without EC2 or provider I/O. An explicitly configured operating store requires the matching immutable marker; legacy stores refuse metadata bearing an unbound operating marker. Controller observation may explicitly read closed records but never authorize a start through that capability.

- [ ] Write failing Moto tests for the 100th/101st dispatch, duplicate reservation, reopened authority, two simultaneous contenders, failed transaction, missing/corrupt marker/record, backwards clock, close/expiry and exact-instance mismatch. Expected: meaningful missing operating behaviour failure.
- [ ] Implement immutable policy validation and transactions against the existing namespace, with no automatic creation/repair/retry. Run `python -m pytest agent/tests/test_operating.py agent/tests/test_lifecycle_dynamodb.py -q`; expect all pass.
- [ ] Commit authority and its verified tests.

### Task 2: Bind actual runtime seams and preserve host qualification

**Files:** Modify `agent/lifecycle/executor.py`, `lambda_runtime.py`, `lambda_entry.py`, `deploy/host_config.py`, `host_bootstrap.py`, `provider_binding.py`; extend existing executor, Lambda runtime/entry and host qualification tests.

**Interfaces:** Optional explicit operating policy in control settings/version-2 control config and version-3 OpenRouter host config. New deployed configuration always includes it. `EC2CommandExecutor(..., operating=None)` reserves the claimed start before the API and checks the window immediately before dispatch. Host admission uses the same configured operating store; observations/stops may proceed closed. Configuration fingerprint includes operating policy only when present; old qualified config tests keep their existing shape.

- [ ] Write failing highest-seam tests proving expired warm handlers/host admission cannot dispatch/reserve/emit work; a closed controller can still observe/stop; pending/uncertain starts are never retried. Include bound config mismatch, missing marker and legacy configuration compatibility.
- [ ] Implement the smallest wiring changes, preserving all existing source/transport checks and startup-only protected-file reads. Run focused lifecycle/Lambda/host qualification tests; expect all pass.
- [ ] Commit runtime binding and tests.

### Task 3: Cloud guard and pure finite deployment documents

**Files:** Create `agent/lifecycle/operating_guard.py`, `deploy/operating.py`, `agent/tests/test_operating_guard.py`, `eval/tests/test_operating_deploy.py`; modify `deploy/lambda_package.py` for a third private `guard` entry and sources.

**Interfaces:** `OperatingGuard` receives validated fixed bindings plus injected AWS clients/clock/DNS probe. `handle({'kind':'guard'})` returns bounded redacted state/receipts; no network on import. Pure `render_operating` produces exact IAM/date-fenced start grant, three schedules, guard environment and least-privilege policy. Guard can never start/renew/recreate resources. Daily credit observation is persisted, missing/stale/bad proof closes; stop actions do not wait for a successful authority write. DNS cleanup stores one immutable absence epoch and rechecks all authorities before same-owned EIP release.

- [ ] Write failing Stubber/fake-backend tests for time/credit/runtime closure, DDB failure with independent Stop, no Start permission, owned identities, two consecutive stop failures, schedule loss, duplicate invocation, CF delay, DNS disagreement/TTL/clock regression and IP ownership mismatch. Reject untrusted events and wrong configurations.
- [ ] Implement guard/pure render/packaging; keep 256MiB/30s/one concurrency and bounded single-attempt SDK calls. Budget each phase so slow cleanup progresses over separate ticks instead of a single unbounded invocation. No receipt claims without observed API results.
- [ ] Run new tests plus lambda-package/cloud-access/observation regressions; expect pass. Commit.

### Task 4: Owned local operator, custody, release preparation

**Files:** Create private `.scratch/december-operation/` explicit operator, tests, immutable owner-approval receipt/manifest and phase ledger; reuse accepted modules by importing pure helpers only, without changing/weakening prior frozen grants. Update `deploy/README.md` with operating contract.

**Interfaces:** Explicit inspect-first CLI phases: preflight, provision disabled controls/guard, enable safety, reserved maintenance start, stage release/custody, DNS/TLS, maintenance stop, invite/wake, desktop/idle verification, handover and cleanup. Every cloud write is exact-owned, receipt-backed and non-replayed after ambiguity. Reuse existing native build/custody mechanisms; bind new release/config report without model requalification. Public allowance `B+0.20`, absolute attempt baseline+100, reserve held outside exposed allowance.

- [ ] Write failing synthetic operator checks for wrong approval hash, expired plan/account, excessive resources/starts/GETs/POSTs, duplicate allocation/stage, lost response and allowance history tampering. Guard/safety schedules must be verified before first Start. Record all policy rulings.
- [ ] Implement explicit phases, log/secret redaction and inspected rollback; preserve old operations and user files. Pin artifact hashes and approval bytes, produce a nonsecret resource/cost preview. Run synthetic operator tests, no cloud writes while local gates incomplete.
- [ ] Run relevant full format/lint/Python/TypeScript/test/build commands from a clean validation checkout with fake credentials/scripted provider, log results. Review the whole branch with one fresh reviewer; fix important findings RED→GREEN. Commit local implementation before cloud apply.

### Task 5: Approved bounded launch and independent handover

**Files:** Private operation receipts and result report/checkpoint/handoff; no unreviewed product edits during activation.

**Consumes:** Passed Task 4 artifacts, exact manifest/approval, fresh AWS identity/Free plan/balance/credits, stopped original host/table and unchanged custody, owner DNS delegation. Authenticated AWS sign-in is available at execution; refresh without upgrade if necessary.

- [ ] Refresh read-only inventory/cost/account/source/custody; first write starts the immutable operating interval, never a moving four-hour legacy acceptance session. Provision only the approved disabled resources and verify independent stop/guard before starting the host.
- [ ] Perform exactly reserved maintenance then real invited cold wake; use fresh native UI observations to edit only app/store A records to the owned new EIP, TTL2h. Verify all authoritative DNS, Caddy trusted TLS, signed readiness, HTTP/OAC refusals and real desktop safety. Count at most two live model requests inside the new shared allowance; retrieve diagnostics before any shutdown/rerun.
- [ ] Close the acceptance browser, observe genuine 60-minute idle stop, reconcile signed accounting and independent AWS state. Hand over private startup link/invites with expiry/limits only after pass. Operating resources intentionally remain within approved bounds; retained storage/IP charges are reported honestly.
- [ ] On failure, close public/model authority and follow owned stop/DNS7200/IP/edge cleanup; do not leave an unverified launch running. At final operating close, cloud mechanisms perform stop independently; operator removes only owned controls after evidence and DNS-safe IP release. No hidden renewed grant or fabricated acceptance.

## Self-review / execution choice

All design sections map to Tasks 1–5; cross-task policy type, marker and phase APIs are named above. Native inline execution was chosen under the owner's explicit "start work till I get back" instruction. Its approval covers code, local tests and conditional launch; do not stall for another execution-method question. A fresh whole-branch reviewer remains required before cloud changes. Record the exact approval message/hash, completed tasks, RED/GREEN evidence and any rulings in the plan-scoped execution ledger.
