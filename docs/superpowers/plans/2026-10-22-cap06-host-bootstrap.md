# CAP-06 explicit host bootstrap implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL superpowers:executing-plans inline,
> TDD and fresh independent final review.

**Goal:** Load restricted immutable host settings and wire owned async host resources.
**Architecture:** Explicit pre-event-loop startup API with exact configuration;
legacy app remains lazy/local, runtime work and health close resources in order.
**Tech stack:** Python, existing FastAPI/HTTPX/boto3/SQLite, Moto offline tests.
**Spec:** docs/superpowers/specs/2026-10-22-cap06-host-bootstrap.md.

## Constraints

- No real AWS/model/credential/resource/key/DNS/TLS calls/writes, deployment or push.
- No implicit environment/backend selection, provider qualification or allowance reset.
- Keep safety and single-worker/generation/cancellation invariants unchanged.
- Existing isolated worktree; Windows cannot establish Linux ACL acceptance.

## Task 1: immutable restricted host settings

- [x] RED eval/tests/test_host_config.py for bounded JSON/exact schema/paths,
      secret files/metadata/parents and immutable validated settings.
- [x] Implement deploy/host_config.py; GREEN without SDK/provider calls.

## Task 2: explicit application environment

- [x] RED agent/tests/test_app_environment.py for import without default creation,
      explicit identity/provider/guard and no ambient/evaluation fallback.
- [x] Add environment mapping and lazy default app in agent/app.py;
      optional mapping in identity_config; GREEN and existing app tests.

## Task 3: owned host assembly and proof

- [x] RED eval/tests/test_host_bootstrap.py using concrete fixtures/Moto for
      default blocked provider, no charges/model calls, lifecycle and cleanup.
- [x] Implement deploy/host_bootstrap.py explicit factory and owned resources;
      closed loops/errors clean up, no double guard; GREEN.

## Task 4: verification and record

- [x] Full affected Agent/host/config/fresh artifact tests and lint/format/pip.
- [x] Fresh independent review, reproduce/fix actionable findings, evidence.
- [x] Checkpoint/handoff and local commit; no activation or gate closure.

## Execution ledger

User's repeated go authorizes continuing inline preparation and routine design
choices in the existing topology. Preflight found default app import can load
ambient local configuration; fix with lazy default and explicit environment map.
Current qualification has no pass artifact; default unqualified verifier gates
both health and work/model admission. No new flag/report schema substitutes it.

Builder check clear. Config missing-module RED then23checks GREEN6.71s. Explicit
environment/import/identity tests3RED then GREEN; legacy settings loader can alter
dotenv flags, so snapshot must follow settings loading (RED401vs404, GREEN).
Bootstrap missing-module RED, initial6tests GREEN3.85s after using HTTPS test
cookies, injected wall clock and typed Snapshot fixture for an owned Task stop.

Ruling: synchronous factory is pre-event-loop only; runtime code root must match
selected release before SDK creation. Synthetic fixtures patch the private root
observation; actual packaged execution/Linux permissions remain unverified. The
optional clock injection follows existing Lambda test practice. No deployment flag.

Review fixes: explicit catalogue encoder and StorefrontService mode still used
ambient configuration; RED/GREEN extends copied environment through both, including
constructor without config. Async service and synchronous Confirmation transports
now ignore environment proxies (routing/argument regressions RED/GREEN).

Review fixes: provider await inside the actor lock starved pending renewal.
RED/GREEN moves it outside lease bookkeeping and uses a shared one-flight1s gate
retaining slow cancellation cleanup. Refresh renews actual pending Moto lease
while verifier is unresolved. Actor authority and local generation/failed/closed
fences follow qualification. Default verifier remains false.

Review fixes: cancelled admission close advanced SDK close before an active pool
worker drained. RED/GREEN retains/shields a full closing task with cancellation-
resistant drain. A second RED/GREEN extends the drain to lifecycle workers sharing
that SDK, including if the earlier app close was interrupted. Final two shutdown
regressions independently2passed3.15s; review clear with no deferred findings.
Latest environment/bootstrap focused19passed9.41s. Earlier broad927then934checks
passed before subsequent regression additions; final source verification is
recorded separately in eval/evidence/cap06-host-bootstrap-20261022.json.

Final all-Agent/host/config/bootstrap/access/browser/fresh artifact verification
936passed/no skips145.06s. ESLint/Prettier, Ruff check/format239files, pip/whitespace
and source hashes pass. No deferred review findings. Local commit only; actual
Linux permissions/keys/packaged execution, launcher integration, Lambda package,
reliable observation/account eligibility/resource approval and qualification stay
open. No cloud/provider/backend/scheduler/allowance activation or push.
