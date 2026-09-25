# 07E grounded discovery implementation

Status: owner-approved Stage 1, implemented and verified on 2026-09-23. Evidence is in PROJECT_CHECKPOINT.md and Ticket 07E. This plan does not open Stage 2.

1. Add explicit public recommendation facts to the existing Controlled Storefront fixtures and expose them at one versioned, read-only route. Test shape, 60-product count, unavailable products, and absence of private state.
2. Extend Structured Intent for hard requirements, soft price preference, and owned-item context with source evidence. Test zero-silent-drop at the Intent Boundary in Arabic, Franco-Arabic, and mixed text, particularly the wedding material/formality/colour/price case. No full-sentence special cases.
3. Add one Agent catalogue reader and deterministic discovery evaluator. Only authoritative facts can satisfy requirements. Unknown is not a match. Prefer 2–3 Exact Matches; otherwise offer labelled Alternatives with explicit misses. Styling uses owned-item context and bounded compatibility rules.
4. Connect catalogue discovery to Shopping Tasks without changing Action authority. Persist structured suggestions in session state and restore them after refresh. Fail closed on catalogue errors.
5. Render safe structured suggestion cards in the Panel, with product facts, labels, and reasons. Preserve Stop, Retry, and lease behavior.
6. Make evaluation completion status language-independent. Rerun focused safety tests, then the three exact owner-written requests through the pinned real-model browser flow. Record facts and failures, not secrets.
7. Run relevant format/lint/test/build checks. Update Ticket 07E and PROJECT_CHECKPOINT.md with verified evidence. Do not close the ticket if the three-request gate fails.

Safety invariants throughout: fixed same-origin catalogue route; no model-authored product IDs, facts, or external URLs; no cart or checkout mutations; stale model work cannot publish suggestions; refresh never replays an uncertain Action.
