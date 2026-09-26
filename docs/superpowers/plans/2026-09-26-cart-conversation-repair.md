# Cart conversation repair

Ticket 14 is on hold while fixing the owner's three manual failures: a completed cart add left the Panel busy, an explicitly named product page prompted unnecessarily, and `عايز 3 كمان من تيشرت اسكندرية` repeatedly asked for rephrasing.

## Reproduction and causes

- A live provider capture correctly returned quantity/increase/3 and the named product for the owner's sentence. Replaying it failed with `Cart operation needs an explicit request`: the boundary required an approved verb despite the explicit quantified desire. The capture is ignored; tests retain the relevant non-secret response shape.
- The browser can report a fractional scroll offset. SnapshotBuilder sent it unchanged although the shared wire contract requires an integer. A failing builder regression reproduced rejection; the earlier service log contained a 422 action-result response after an add. This establishes a reproducible cause of the symptom, though the exact historical rejected body was not retained.
- The Panel ignored the rejected result promise, so a changed cart could leave the task waiting silently. A failing Panel regression reproduced that omission.
- The opening request used `وديني` and colloquial spelling of the actual catalogue name `تيشيرت إسكندرية`. The matcher and opening vocabulary did not recognize this combination. Name normalization is shared with cart-line matching and still requires one unambiguous matching item.
- Quantity/removal planning assumed the cart was already visible. It now navigates to the same-origin cart and plans from the resulting fresh Snapshot before editing.

## Behavior and boundaries

SnapshotBuilder rounds scroll offsets at the producer. Rejected result delivery visibly reports uncertainty and stops queued execution without replaying the mutation. The Shopper can inspect the cart and Stop. Cart quantities retain explicit amount and direction validation; model output cannot turn a relative delta into an absolute total. Opening an explicitly named verified product no longer needs a redundant question for the repaired request. Unusable model drafts get at most one rephrasing attempt, followed by an explicit Stop handback; this is bounded failure, not a claim that interpretation always succeeds.

Scope excludes Ticket 14, broad architecture refactors, model/provider changes, and spending-cap increases. Unrelated proposal documents and the user's generation script are preserved.

## Verification

The regressions exercise the captured response through the real HTTP interpretation/task flow against one and three cart lines, including a product-page start, exact increment, completion and duplicate-result handling. A browser regression exercises fractional scrolling, actual add, subsequent quantity change from the product page, completion, and Undo. Foreign-origin cart navigation is rejected before any edit.

Independent Standards review requested the foreign-origin regression; it was added and passed. Spec review found that newly accepted `less` / `أقل` / `زيادة` wording needed consistent direction checks. Those tests failed before the repair and passed afterward. The reviewer independently passed all 17 conversation-repair tests and reported no remaining finding. Final full-suite and live evidence is recorded in PROJECT_CHECKPOINT.md.

The full Python run exposed a cart hydration race (423 passes, one failure): the initial state fetch replaced identical server-rendered controls after the navigation Snapshot. The next input Action was blocked against a detached element. The same cart browser suite passed all 10 tests after preserving identical markup; isolated review found no defect. Final affected Agent checks passed 59 tests. All 150 TypeScript tests passed. No additional whole-workspace run was performed after this targeted fix.

Live verification passed `وديني لصفحة تيشرت اسكندرية`, `ضيفهولي فالعربية` with completion, and `عايز 3 كمان من تيشرت اسكندرية` from the product page, reaching quantity 4 from 1. Recommendation setup unnecessarily asked for the supplied budget again; that separate known limitation remains open rather than being hidden by a green cart result.

The same live increase request also passed with three products: clothing-06 changed 4 → 7 while shoe-09 and clothing-05 stayed at 1 each. Demo services remain running with this clearly test-created cart. Six live requests were used for this verification (including the repeated budget answer), plus one earlier captured diagnostic request; subsequent diagnostic replays used the saved response without spending.
