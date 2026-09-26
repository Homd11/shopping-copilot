# Soft recommendation preferences and bounded chat

The owner prioritized these repairs before Ticket 14. Architecture refactoring remains deferred.

## Approved behavior

- Subjective phrases such as “كويس كده”, “nice”, and “7elw” may guide a recommendation without becoming mandatory catalogue features.
- Optional preference metadata must not invalidate an otherwise valid request. Explicit product type, feature, size, color, price, and cart authority still require grounded validation.
- Recommendations explain actual catalogue facts and prices. Alternatives identify unmet requirements; the Copilot does not claim unsupported superiority or comfort.
- Preserve the strict Action, Confirmation, Sensitive Field, origin, refresh, and duplicate-delivery boundaries.
- Redesign the chat with a bounded conversation scroller, persistent composer and Stop, improved Arabic typography, blue palette, accessible focus, and readable product/question cards. Messages must not stretch the page or move the Storefront.
- Desktop and mobile keep the Storefront reachable. Voice disclosure and editable transcription remain intact. Suggested starter requests fill the draft without sending it.

## Verification

Focused interpreter, catalogue, and cart tests passed (132). Two bounded live OpenRouter calls passed with schema 7 / intent-v17: the owner's exact vague football-shoe request preserved its 2000 EGP budget without an invented comfort requirement; an explicit “مريح” request retained the comfort requirement. No additional prose-generation call is added.

The browser layout regression reproduced the original document-growth bug before the CSS change. It checks 60 messages at 1280×900, 390×844, and 390×640, including the visible recording fallback. Desktop and mobile screenshots are ignored local artifacts in `eval/reports/chat-redesign/`.

The first full Python run passed 400 tests and exposed two benchmark-scoring mismatches: the new empty optional list was included when older corpus expectations omitted it. Default normalization now handles that list consistently with other optional fields; the nine benchmark tests pass. Final clean-suite evidence is recorded in `PROJECT_CHECKPOINT.md`.

## Standards review

No confirmed hard standards or safety-boundary violations. The reviewer requested v7 cart regressions and flagged recommendation scrolling. The relative-quantity tests now exercise both v6 and v7; the layout regression drives actual controller events, rather than only a synthetic long history. Broad class refactors remain deliberately deferred.

## Spec review

Two findings were fixed. First, absence from known vocabulary did not establish that a phrase was subjective: a model could mislabel “waterproof” and erase it. Discarding an invented requirement now additionally requires a positive, whole-span quality cue. Unknown concrete or mixed phrases remain rejected rather than silently softened. Second, recommendation insertion preserves the prior reading position and shows the first card to a Shopper following the conversation; a completion message cannot move it out of view. Retry and takeover receive focus as actionable questions do. The focused follow-up review found no remaining actionable defect.

Review totals: Standards — no confirmed hard violations, two bounded coverage/UX notes addressed. Spec — two findings fixed; no remaining actionable findings. Ticket 14 remains the next ordered implementation ticket after this owner-requested repair and visual pass.
