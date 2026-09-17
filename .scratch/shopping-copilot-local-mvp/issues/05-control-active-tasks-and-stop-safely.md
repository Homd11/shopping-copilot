# 05 — Control active tasks and Stop safely

**What to build:** Make one active Shopping Task pause, resume, reject stale results, and stop without allowing any later Action to affect the Storefront.

**Blocked by:** 03 — Run a Shopping Task through the Panel.

**Status:** resolved

- [x] A session permits one active Shopping Task and rejects a second unless replacement explicitly cancels the first.
- [x] A Shopper question pauses the same task and resumes only from its matching answer.
- [x] Action Results resume a task only when task identity, Action identity, and sequence all match the pending Action.
- [x] Duplicate results are idempotent and stale or mismatched results have no effect.
- [x] Stop atomically cancels pending waits, clears queued Actions, and prevents every later Action emission.
- [x] Repeated ineffective Actions, timeouts, and the eight-step cap pause for Shopper direction instead of looping.
- [x] Deterministic tests exercise cancellation before and after every wait boundary.

## Comments

- Implemented active-task replacement, matching answers/results, idempotency, Stop propagation into the Bridge ledger, and bounded pause behavior.
- Verified with Agent, Panel, and Bridge regression suites.
