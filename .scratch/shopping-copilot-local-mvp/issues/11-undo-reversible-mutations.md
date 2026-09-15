# 11 — Undo Reversible Mutations

**What to build:** Make cart additions, quantity changes, and single-line removal immediate and recoverable through an exact localized Undo rather than Confirmation.

**Blocked by:** 05 — Control active tasks and Stop safely; 09 — Enforce the core safety boundary.

**Status:** ready-for-agent

- [ ] Adding an available item, changing quantity, and removing one line are classified as Reversible Mutations.
- [ ] Removing the final cart line remains reversible and does not become an implicit bulk-clear Action.
- [ ] The Storefront updates optimistically and displays a localized, accessible ten-second Undo toast describing the exact change.
- [ ] Undo restores the precise cart state that existed before the Reversible Mutation.
- [ ] Consecutive quantity changes on the same line coalesce into one Undo that restores the pre-burst quantity.
- [ ] A rejected optimistic update automatically restores prior state, removes Undo, and reports failure.
- [ ] The Copilot reports success only after the Storefront confirms the Mutation.
- [ ] Deterministic and browser tests cover success, Undo, coalescing, last-line removal, and failure recovery.
