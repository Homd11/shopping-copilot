# 12 — Recover Mutation state across refresh

**What to build:** Preserve pending questions and the remaining Undo opportunity across refresh while invalidating old Confirmation and refusing uncertain Mutation replay.

**Blocked by:** 06 — Resume a Shopping Task after refresh; 10 — Confirm Guarded Mutations exactly; 11 — Undo Reversible Mutations.

**Status:** ready-for-agent

- [ ] A pending Shopper question returns after refresh with the same identity and resumes the original Shopping Task.
- [ ] An active Undo toast returns with only its remaining duration; refresh never restarts the timer.
- [ ] Undo after refresh restores the same exact prior cart state.
- [ ] Every unused Confirmation is invalidated by refresh and must be requested again from reconciled state.
- [ ] The Storefront remains authoritative when the Shopper changes cart or filters directly during a paused task.
- [ ] A Mutation with an uncertain recorded outcome is never replayed automatically.
- [ ] Refresh tests cover each interruption point before, during, and after Reversible and Guarded Mutations.
