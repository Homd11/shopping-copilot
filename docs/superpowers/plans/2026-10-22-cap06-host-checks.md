# CAP-06 concrete host checks implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL superpowers:executing-plans inline,
> TDD and one fresh final review.

**Goal:** Supply concrete release, service, remote admission and allowance checks.
**Architecture:** Existing host aggregate consumes bounded async check callbacks;
file/SQLite I/O stays off-loop and fixed private HTTP is intercepted in tests.
**Tech stack:** Python/HTTPX/SQLite, existing Moto test authority.
**Spec:** docs/superpowers/specs/2026-10-22-cap06-host-checks.md.

## Constraints

- No AWS/model/credential/resource/DNS/TLS write or new scheduler/service.
- No qualified-provider default or new qualification artifact format.
- No reset/retry/refund/enable, mutable authority rebinding or Agent health recursion.
- Existing worktree, local commit only; bootstrap/configuration remains pending.

## Task 1: remote authority health seam

- [x] RED tests in agent/tests/test_async_boundary.py for ready metadata-only read,
      lost/mismatched authority and no quota/grant/activity writes.
- [x] Add DynamoInvitationStore.check and AsyncAdmissionPolicy.ready; GREEN.

## Task 2: concrete check resource

- [x] RED eval/tests/test_host_checks.py for release fingerprint/tampering,
      external catalogue/revision, private authenticated bounded HTTP, actual
      allowance enabled/reservation headroom and binding changes/closed resource.
- [x] Implement deploy/host_checks.py, bounded off-loop I/O and five callback map
      with explicit async provider or unqualified_provider; GREEN.

## Task 3: integrated proof and evidence

- [x] ASGI signed-health tests using concrete fixtures, explicit false provider,
      no mutation/paid calls and post-HTTP catalogue revalidation; fresh packaging.
- [x] Relevant all-Agent regressions, lint/format/pip/diff and fresh review.
- [x] Record evidence/checkpoint/handoff, local commit; no gate closure/deployment.

## Execution ledger

Continuing under existing authorization for local preparation. The current gate
has no approved Bedrock qualification artifact; keep it explicitly false rather
than define a new pass format. Build four concrete checks as a complete bounded
slice before the host configuration/bootstrap can select them. No topology change.

Builder check clear. Admission readiness missing-method RED,4checks GREEN.
HostChecks missing-module RED; concrete checks22passed9.27s. HTTP fixtures use
raw AsyncByteStream so the raw-byte cap is exercised (not already-consumed mock
bodies). Explicit short pytest parameter IDs avoid Windows environment length
overflow for oversized-body cases. Valid cloned admission-store replacement
reproduced silent rebinding RED; pin store/client/table/namespace/identity then
GREEN. Final initial focused suite32passed11.09s. Full checks/review follow.

Final fresh review clear:32concrete/boundary+19existing host checks independently
passed. All-Agent/concrete/access/browser and fresh release packaging894passed,
no skips139.37s. ESLint/Prettier, Ruff check/format234files, pip and whitespace pass.
Evidence:eval/evidence/cap06-host-checks-20261022.json. No deferred findings or new
authorization; actual bootstrap/provider qualification/scheduler/package remain
pending. Local preparation commit only, no push.
