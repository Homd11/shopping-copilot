# 05 — Control active tasks and Stop safely

**What to build:** Make one active Shopping Task pause, resume, reject stale results, and stop without allowing any later Action to affect the Storefront.

**Blocked by:** 03 — Run a Shopping Task through the Panel.

**Status:** ready-for-agent

- [ ] A session permits one active Shopping Task and rejects a second unless replacement explicitly cancels the first.
- [ ] A Shopper question pauses the same task and resumes only from its matching answer.
- [ ] Action Results resume a task only when task identity, Action identity, and sequence all match the pending Action.
- [ ] Duplicate results are idempotent and stale or mismatched results have no effect.
- [ ] Stop atomically cancels pending waits, clears queued Actions, and prevents every later Action emission.
- [ ] Repeated ineffective Actions, timeouts, and the eight-step cap pause for Shopper direction instead of looping.
- [ ] Deterministic tests exercise cancellation before and after every wait boundary.
