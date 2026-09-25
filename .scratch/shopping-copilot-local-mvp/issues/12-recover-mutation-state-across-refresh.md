# 12 — Recover Mutation state across refresh

**What to build:** Preserve pending questions and the remaining Undo opportunity across refresh while invalidating old Confirmation and refusing uncertain Mutation replay.

**Blocked by:** 06 — Resume a Shopping Task after refresh; 10 — Confirm Guarded Mutations exactly; 11 — Undo Reversible Mutations.

**Status:** resolved

- [x] A pending Shopper question returns after refresh with the same identity and resumes the original Shopping Task.
- [x] An active Undo toast returns with only its remaining duration; refresh never restarts the timer.
- [x] Undo after refresh restores the same exact prior cart state.
- [x] Every unused Confirmation is invalidated by refresh and must be requested again from reconciled state.
- [x] The Storefront remains authoritative when the Shopper changes cart or filters directly during a paused task.
- [x] A Mutation with an uncertain recorded outcome is never replayed automatically.
- [x] Refresh tests cover each interruption point before, during, and after Reversible and Guarded Mutations.

## Verification

The browser refresh test restores a two-product cart through Undo with a decreasing server deadline. Agent recovery tests cover the same pending question identity, invalidated and renewed cart-revision-bound Confirmation, mutation interruption before/during/after execution, and rejection of a late Action Result. The Panel serializes overlapping recovery snapshots and sends its latest Storefront Snapshot on Retry. Refresh during navigation or field entry permits fresh-state Retry; an in-flight or unverified mutation permits Stop and a new request, never re-planning the old mutation. The browser also verifies Stop-only recovery after an unverified add.

Full workspace: 138 TypeScript and 374 Python tests passed. Build, ESLint, Ruff lint/format, changed-file Prettier, and diff checks passed. The repository-wide Prettier check still flags six untouched pre-existing files.
