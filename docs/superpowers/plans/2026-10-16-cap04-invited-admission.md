# CAP-04 invited admission implementation plan

> **For agentic workers:** Use superpowers:executing-plans inline. The owner explicitly requested implementation of approved local ticket04, without contacting testers.

**Goal:** Implement owner-issued access codes and bounded AI access locally, with no real testers, paid inference or cloud changes.

**Architecture:** A focused admission package owns persistent hashed invitations, browser-bound grants, fixed UTC windows and owner CLI. Existing Shopper HTTP authority remains authoritative for cart/session ownership. An outer ASGI boundary limits bodies, rates, HTTP concurrency and SSE connections; the Panel gates AI initialization behind a code exchange while Storefront browsing remains available.

**Tech stack:** Existing Python SQLite/asyncio/FastAPI and TypeScript Panel; no new dependencies.

**Spec:** `docs/cap04-spec.md`, `docs/cap04-ticket-breakdown.md` local04, approved 11/14 October design.

## Global constraints

- Preserve Confirmation, Sensitive Fields, off-origin, tab lease and uncertain-Action protections; admission never grants cart/session authority.
- No prompt, interpreter, catalogue retrieval or provider payload changes; tests use scripted/fake providers and pre-agreed HTTP/browser/storage seams. Local authorization callbacks at provider entry are necessary to enforce revocation across asynchronous queues and key checks.
- Production requires explicit admission settings even for scripted rehearsals; local development is opt-in. Real codes are created later by the owner; no messaging participants.
- Single Agent worker; persistent storage lives outside releases. Missing/corrupt initialized admission storage refuses access, never reinitializes.
- Initial operating examples are finite bounds, not a measured EC2 capacity claim. Automatic wake/control-store integration belongs to ticket07.

## Review focus

1. Two processes redeeming the final code slot: exactly one succeeds; repeats in the same admitted browser do not consume new slots.
2. Revocation/expiry during SSE or in-flight inference: no further paid invocation or Action delivery; Stop remains possible for the owner.
3. New cookies, chunked bodies and abandoned EventSource connections cannot bypass global bounds or leak slots.
4. Refresh/restart cannot renew absolute windows or replenish redemption/session quotas; foreign session access still returns404.
5. Code input never enters URLs, persistence, diagnostics or the LLM; busy/expired screens keep storefront browsing available and do not auto-submit retries.

## Task1: Durable invitations and owner controls

Files: create `agent/admission/store.py`, `agent/admission/__main__.py`, `agent/tests/test_admission.py`.

- [x] Write/run failing public store tests for window, final-slot concurrency, restart, revocation and missing/corrupt storage.
- [x] Implement explicit exclusive initialization with identity, SHA256 random-code lookup, atomic grant redemption and bounded durable per-code session creations. Grant subject hashes browser authority plus Storefront context; quotas never reset on process restart.
- [x] Owner CLI initializes, issues fixed-window codes, lists safe metadata and revokes by public ID. Raw generated codes are printed only by explicit local issue; no HTTP admin API.
- [x] Focused tests pass; record decisions for the combined commit below.

## Task2: HTTP and inference authority

Files: create `agent/admission/runtime.py`, `agent/admission/limits.py`; modify `agent/shopper_http.py`, `agent/app.py`, public-runtime tests.

- [x] HTTP regression denies session/messages/events/results before admission, expires/revokes grants, preserves foreign ownership and safe Stop; fake-provider count proves no paid work after denial.
- [x] Configure explicit finite global/per-browser request rates, body size, active request/SSE/session limits. Reject excess immediately (waiting capacity zero); existing inference queue remains ticket05's authority.
- [x] Exchange code in bounded CSRF-protected POST after existing linking. Return safe admission status; verify grant on each HTTP route, each SSE delivery and before/after asynchronous model phases.
- [x] Wrap shared model client to recheck request-bound admission before every repair/advice/model invocation; no prompt changes. Configure production fail-closed and preserve unconfigured local development.
- [x] Focused HTTP/storage/concurrency tests pass; update existing production fixtures with explicit test admission config; prepare the combined commit below.

## Task3: Panel entry and combined proof

Files: create `panel/src/admission.ts`; modify `panel/src/main.ts`, `panel/src/styles.css`, `deploy/README.md`, `.env.example`; add browser acceptance in `eval/tests/test_admission_browser.py`.

- [x] Render code form after Shopper linking and before controller.start; keep code ephemeral, clear input after POST, show denied/expired/busy messages, allow explicit retry without auto-submission.
- [x] Distinguish admission errors from Shopper identity loss, stop/cancel Panel execution safely on revoked streaming authority and offer code entry again. Surface bounded busy responses without duplicating Actions.
- [x] Browser proof with two contexts and scripted services: denied before code, accepted navigation, refresh retains admission, foreign cart isolated, code absent from URLs/storage, revocation closes access, fixed expiry survives reopen.
- [x] Stop owned manual services for full suite; relevant format/lint/type/build/full tests once, independent Spec/Standards reviews, fix findings with regressions.
- [x] Document operating limits and owner commands, checkpoint/close local ticket04 only when accepted, commit locally; no push/deployment or real codes without separate instruction.

## Decisions

Owner approved the existing ticket/design and asked to implement it now. Use inline execution; do not reopen already-settled invitation policy questions. Total per-code session-creation quota is deliberately durable (not replenished at restart); active process sessions have an additional configurable cap. After Agent restart the existing browser authority resets, so a fresh admission consumes a remaining redemption; absolute invitation expiry remains unchanged.

Storage, HTTP and Panel changes are reviewed and committed together because their
authority contract spans these boundaries. This replaces the planned per-slice
commits; focused tests still run after each slice. The model request's optional
authorization callback stays local and is never serialized. Queue acquisition and
provider key checks can await, so entry checks must run after them as well as at
the HTTP boundary. Paid server speech remains disabled under admission until it
has equivalent accounting and authorization checks.

Independent Spec/Standards review found two issues, both reproduced and fixed:
revocation during awaited Storefront validation could release an already queued
Action, and terminal SSE429 lacked an explicit recovery control. A subsequent
full suite exposed an early-Snapshot/two-tab restoration race; reconciliation now
waits for established task ownership, with a deterministic controller regression.
Both reviewers cleared that narrow follow-up. Final checks below establish local
ticket closure.

The serial full run also exposed an existing evaluation setup race: manual iframe
navigation could run before Panel initialization assigned its initial URL. The
evaluation helper now waits for the ready Panel and awaits Frame navigation.
The final regression delays the real Panel startup trigger and reproduces the
failure against the old helper; preliminary synthetic-frame fixtures were
discarded. Both review axes cleared the final test-only change. No runtime
shopping behavior was changed to accommodate the test.

## Final verification

- `python -X utf8 -m pytest agent/tests eval/tests -q -x --tb=short`: 686 passed in 549.35s.
- `pnpm --recursive test`: 199 passed (Bridge 97, Storefront 63, Panel 39).
- Recursive builds and `tsc --noEmit`, ESLint, Ruff and repository Prettier checks pass.
- Owner CLI smoke tests and isolated production-probe help pass. No HTTPS trust changes or deployed/paid qualification performed.

## Standards

No unresolved findings. The post-await revocation finding was reproduced and
fixed; the final Panel ownership and evaluation-harness changes were cleared.

## Spec

No unresolved findings. Explicit SSE429 recovery was added and verified; local
admission remains separate from Shopper/Action authority and cloud acceptance.

Local ticket 04 is resolved. Parent CAP-04 remains open; next local step is 06.
The branch is committed locally without push or participant contact.
