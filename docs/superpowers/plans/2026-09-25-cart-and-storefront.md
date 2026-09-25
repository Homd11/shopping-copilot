# Tickets 11 and 11B implementation plan

**Goal:** Deliver the approved cart journey with exact ten-second Undo, then polish the Arabic-first graduation demo.
**Execution:** Native in the existing checkout, as requested; preserve prior work. Architecture-report refactors are deferred.
**Scope authority:** Approved local MVP spec and tickets 11/11B. In-memory local commerce only; no new frameworks, provider calls, or production work.

## Ticket 11

- [x] Add HTTP-level regressions for available add, variant validation, quantities, last-line removal, exact Undo, coalescing, expiry, stale/duplicate requests, and guarded-state invalidation.
- [x] Extend `store/src/guarded-cart.ts` with revision-bound reversible edits and one current Undo record. Quantity edits to the same line retain the original prior state and original expiry; other edits replace the record. Guarded changes invalidate Undo.
- [x] Implement `/cart/state`, `/cart/items`, `/cart/quantity`, `/cart/remove`, `/cart/undo` in `store/src/app.ts`. Require an operation ID and revision; never replay an uncertain change.
- [x] Add product options and cart controls in `store/src/views.ts`. Add a small browser script for optimistic feedback, server reconciliation, rollback, localized Undo, and disabled pending controls. Keep existing semantic labels and guarded forms intact.
- [x] Extend intent and deterministic task planning for ordinary cart edits using the current product/cart controls. Verify the Storefront result before completion; ambiguous targets hand back safely. Never treat last-line removal as bulk clear.
- [x] Run focused Storefront/Agent checks and complete browser shopping flows, including a rejected optimistic update and expired Undo.

## Ticket 11B

- [x] Preserve selectors while adding a restrained cream/ink/terracotta retail layout, clear price/stock/options, responsive product cards, and legible checkout/cart summaries using local CSS.
- [x] Visually inspect home, category, product, cart and checkout at desktop and mobile widths; check focus, overflow and reduced motion.
- [x] Run full tests, build, lint and changed-file format checks; update both tickets and the checkpoint with evidence.

## Review focus

- Concurrent edits cannot restore the wrong prior cart.
- Undo expiry uses the server clock and never restarts on quantity coalescing.
- Duplicate operations and stale revisions cannot apply twice.
- An uncertain network outcome never triggers automatic replay or success narration.
- Existing confirmation authority expires when cart state changes; Sensitive Fields remain excluded.
