# 06 — Resume a Shopping Task after refresh

**What to build:** Restore a Shopping Task after browser refresh, reconcile current Storefront state, avoid uncertain replay, and keep Action execution under one tab's control.

**Blocked by:** 05 — Control active tasks and Stop safely.

**Status:** ready-for-agent

- [ ] Refresh restores the visible conversation, current task status, and any pending Shopper question.
- [ ] The browser reconnects using opaque session and event identifiers and supplies a fresh Snapshot before resumption.
- [ ] No new Action is emitted until the active task and current Storefront state have been reconciled.
- [ ] An Action whose outcome cannot be proven is marked uncertain and is never replayed automatically.
- [ ] One tab owns the execution lease; another tab requires explicit takeover before it can resume Actions.
- [ ] A clear Reconnecting state disables new task input and Actions until recovery resolves.
- [ ] An inactive resumable session expires after thirty minutes without clearing Storefront cart state.
