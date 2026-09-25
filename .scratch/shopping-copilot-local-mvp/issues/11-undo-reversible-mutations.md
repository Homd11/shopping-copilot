# 11 — Undo Reversible Mutations

**What to build:** Make cart additions, quantity changes, and single-line removal immediate and recoverable through an exact localized Undo rather than Confirmation.

**Blocked by:** 05 — Control active tasks and Stop safely; 09 — Enforce the core safety boundary.

**Status:** resolved

- [x] Adding an available item, changing quantity, and removing one line are classified as Reversible Mutations.
- [x] Removing the final cart line remains reversible and does not become an implicit bulk-clear Action.
- [x] The Storefront updates optimistically and displays a localized, accessible ten-second Undo toast describing the exact change.
- [x] Undo restores the precise cart state that existed before the Reversible Mutation.
- [x] Consecutive quantity changes on the same line coalesce into one Undo that restores the pre-burst quantity.
- [x] A rejected optimistic update automatically restores prior state, removes Undo, and reports failure.
- [x] The Copilot reports success only after the Storefront confirms the Mutation.
- [x] Deterministic and browser tests cover success, Undo, coalescing, last-line removal, and failure recovery.

## Verification — 2026-09-25

Full workspace: 137 TypeScript tests and 317 Python tests passed, including Tickets 09/10 safety and Ticket 11 manual/Copilot browser journeys. Build, lint and format checks passed. Review findings were fixed; see `docs/superpowers/plans/2026-09-25-cart-review.md`. Five Storefront pages were visually checked at desktop/mobile widths. Scripted browser evidence does not claim live-provider reliability.
