# Tickets 11 and 11B review

Scope: current cart and Storefront polish additions on top of the existing uncommitted Tickets 07–10. Architecture-report refactors remain deferred. Standards and Spec reviews ran independently, followed by focused corrections.

## Standards

- Fixed: the real-provider request still advertised schema 4 although cart intents require schema 5. Both request metadata and the response schema now agree; request-contract tests cover this boundary.
- Fixed: model-suggested size/color could replace selected variants without Shopper evidence. Overrides now require bounded literal evidence in the current message (Arabic digits normalized); absent constraints retain current selections. Unsupported translated variants fail closed rather than guessing.
- The reviewer rechecked both repairs and found no remaining issue in those fixes.

## Spec

- Fixed: Undo described only the operation. It now identifies the product, variant and original/current quantities, including the pre-burst quantity for coalesced changes.
- Fixed: optimistic cart changes left totals and line counts stale. The pending view updates the badge, visible lines, status and exact-money total; rejected edits reconcile to Storefront state without offering Undo or replaying a mutation.
- Fixed: replacing cart HTML lost keyboard focus. Equivalent controls regain focus; removal moves focus to Undo after controls are enabled. Browser regressions verify quantity focus and removal focus.
- Undo descriptions are announced politely and associated with the Undo control. The timer does not create repeated screen-reader announcements.

Findings: Standards 2 (both fixed; worst initial priority P1), Spec 3 (all fixed; worst initial priority P2). No architecture expansion.

## Verification scope

HTTP checks cover chosen variants, precise Undo, coalescing/deadline, invalid/stale/duplicate edits, last-line removal and invalidation of guarded authority. Agent checks cover sourced intents and confirmed versus rejected outcomes. Browser checks cover manual and Copilot cart journeys, rollback, expiry and focus. Existing Tickets 09/10 safety regressions remain required. Desktop/mobile screenshots are local evaluation artifacts under `eval/reports/ticket11b/`; the five main pages were inspected at 1280px and 390px with overflow, keyboard focus and reduced-motion checks.

Provider request/validation contracts are tested; this change does not claim a new live-provider reliability run. The Storefront remains a local, in-memory fictional shop. Ticket 12 remains the next recovery task.

Final full workspace verification: `pnpm test` passed all 137 TypeScript and 317 Python tests. Build, ESLint, Ruff lint/format, changed-file Prettier and diff checks passed.
