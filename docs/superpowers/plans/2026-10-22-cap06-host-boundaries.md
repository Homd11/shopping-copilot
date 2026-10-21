# CAP-06 host boundary implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL superpowers:executing-plans inline,
> TDD, one fresh final review.

**Goal:** Connect async remote authority/work and signed health to injected Agent.
**Architecture:** Bounded off-loop datastore I/O, event-loop state, awaitable hooks.
**Tech stack:** Existing Python/asyncio/FastAPI/boto3, pytest/Moto and ASGI tests.
**Spec:** docs/superpowers/specs/2026-10-22-cap06-host-boundaries.md.

## Global constraints

- No AWS/model/resource/key/DNS/TLS/provider activation or new service.
- No I/O on Agent event loop, unbounded queue, backend retry or uncertain replay.
- Preserve local interfaces, ownership, confirmation, lease and refresh invariants.
- No default readiness truth, qualification invention or signed health code logging.

## Review focus

- Cancelled queued/entered calls retain real bounded capacity (Task 1).
- Async grants cannot become truthy coroutine authority or survive owner change (Task 1).
- Known/pending/unknown leases and abandoned begin cleanup differ (Task 2).
- Post-await generation/state changes invalidate readiness (Task 3).
- Lifespan/model/streaming paths await hooks and preserve local behavior (Task 3).

## Task 1: async admission boundary

Create agent/async_boundary.py and agent/admission/async_runtime.py, tests
agent/tests/test_async_boundary.py. Add Policy redemption/allocation wrappers and
async ShopperAccess ownership helper; route/app awaitable updates belong Task 3.

- [x] Write/run RED for bounded thread capacity, cancellation and responsiveness;
      async policy allowance/redemption/session semantics and ownership changes.
- [x] Implement bounded I/O/invoke and policy wrappers; run GREEN.

## Task 2: async lifecycle actor

Create agent/lifecycle/async_work.py and agent/tests/test_async_work.py;
add DynamoLifecycle.check_work read-only authority check.

- [x] Write/run RED for initialize, pending transfer, cancelled begin, capacity,
      expiry/generation fences, meaningful-only activity and graceful close.
- [x] Implement serialized async lifecycle actor using one bounded I/O worker;
      run GREEN with Moto and event/thread gates.

## Task 3: ASGI readiness and awaited integration

Create agent/lifecycle/host_health.py, agent/tests/test_host_boundaries.py; modify
agent/app.py and shopper_http.py for awaited sync/async hooks and explicit factories.

- [x] Write/run RED for signed ASGI health, mandatory checks, invalid proof,
      post-await state changes, HTTP remote admission/work and normal local routes.
- [x] Implement trusted aggregate and hooks, await all authority use including
      model/Action delivery; run focused regressions GREEN.

## Task 4: verify and record

- [x] Fresh release packaging plus affected admission/ownership/model/Action,
      lifecycle/readiness/recovery safety regressions; repo lint/format/pip/diff.
- [x] Fresh independent review, RED/GREEN fixes, exact evidence and handoff updates.
- [x] Commit locally only; actual bootstrap checks/package/scheduler stay pending.

## Execution ledger

Ruling: go authorizes continued inline preparation in the existing isolated
worktree. Async admission is included because wiring remote lifecycle while
blocking on remote invitation reads would not meet the host integration contract.
No cloud factory is selected by the existing application environment.
Pre-flight: invoke spans Policy/Work hooks; actor owns event-loop SessionStore;
HostReadiness authenticates before actor/status and trusted dependency checks.

Tasks1/2: missing-module REDs observed, initial8checks GREEN. Additional capacity,
generation/startup and expiry/cleanup checks now exercise the same boundaries.
Task3: missing-host-module RED observed; initial integrated admission/ownership
and health suite30passed. Added deadline/startup/post-await identity checks.

Review ruling: fresh reviewer reproduced a2.203second health response because
asyncio.timeout waited for gather cancellation cleanup. Explicit regression RED,
then retained single aggregate across both authority reads/checks/cleanup and
asyncio.wait deadline GREEN. Timeout returns false while cleanup holds capacity;
lifespan drains health before work. This implements the bounded response contract
without assuming that cancellation cleanup is immediate.

Verification ruling: first broad run862passed, one competing-executor failure and
its pending-stub teardown error. Deterministic Moto-only interleaving reproduced
one successful claim receipt but stored command restored to pending by the loser's
whole-table rollback. The installed Moto transaction implementation backs up and
restores the entire table without thread isolation. Only that test's mock server
transactions are serialized; a barrier still forces two controller claims from
the same revision. No production executor/lifecycle arbitration lock was added.
The next broad run863passed with one concurrent-wake mock rollback failure (a
successful generation1 receipt followed by stored generation0). Generalized the
mock atomicity fix into the shared lifecycle Moto fixture, covering each get,
query and transaction operation. Removed the duplicate executor transaction lock;
its first-two-claims barrier remains. No controller workflow is serialized.

Review ruling: the new aggregate Task completion await could observe work.failed
after a successful aggregate. A call_soon failure reproduced signed ready=true;
RED/GREEN added a final synchronous closed/failed/generation fence before signing.
Fresh review now clear: both original reproductions and host tests21passed8.06s;
fixture/concurrency recheck5passed6.29s. Final focused remote authority/executor/
new host suites96passed36.94s. Final broad verification and reviewer recheck are
recorded in eval/evidence/cap06-host-boundaries-20261022.json.

Final broad run865passed/no skips119.85s including every Agent test and a fresh
release build. ESLint/Prettier, Ruff check/format232files, pip and whitespace pass.
No deferred review findings; no AWS/model/resource/key/DNS/TLS write, backend
activation, quota or allowance reset/increase, scheduler addition or push.
