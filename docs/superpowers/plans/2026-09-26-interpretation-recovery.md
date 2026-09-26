# Recommendation follow-up and interpretation recovery

The owner's sister completed a recommendation request, then “افتح صفحة القميص الرسمي” failed. A bounded live replay reproduced the actual failure: the provider selected verified `clothing-05` but omitted `navigation_source`. The prior validator rejected it before any navigation. The exact captured response now passes the interpreter regression without another paid call.

## Behavior

- Ground product identity against previously verified recommendations and current Shopper words. Normalize Arabic diacritics and definite articles across product names; no individual product-name exception is added.
- Treat model source quotations as redundant for a uniquely named product page. Unknown IDs, conflicting names, unrelated references, ambiguous names, and negated opening requests cannot silently choose a product.
- Ask with verified product choices when a reference is unclear. Exact choices are bound to the active question and resolve deterministically without another model call. Stale questions are rejected.
- Unusable model drafts, including malformed JSON or rejected authority, produce a harmless rephrasing question instead of a Retry loop. Discard unvalidated authority, interpret the answer as a fresh request, and preserve verified recommendation context. Never execute a rejected Action.
- Provider/network/budget failures retain their existing paused flow. Stop, refresh recovery, single-use Confirmation, mutation validation, and uncertain-outcome rules stay enforced. Repeated invalid drafts end with a working Stop at the task limit.
- Arabic clarification fields are localized and receive focus.

## Evidence and limits

The captured failure was reproduced before editing; six initial regression cases failed on the old behavior. Focused tests now cover missing metadata, Arabic name normalization, malformed drafts, mutation misclassification, refreshed choices, duplicate answers, negation and unrelated products, and the task cap. This improves recovery for unseen invalid drafts; it does not guarantee every natural-language request is interpreted correctly. No automatic model retry or additional prose-generation call is introduced. Ticket 14 remains deferred until this repair is verified.

Full verification and independent review results are recorded in PROJECT_CHECKPOINT.md.

## Final verification and review

- Complete workspace run: 148 TypeScript tests and 413 Python tests passed, including deterministic browser tests. Prettier, ESLint, Ruff lint/format, Panel typechecking and all builds passed.
- Standards review: no actionable findings. Spec review found two navigation-authority gaps: a page noun could accept a locate request, and curly apostrophes/Arabic vowel marks could bypass negative wording. Both were fixed with three additional regressions. The final affected suites passed 135 tests; follow-up review independently passed all 14 recovery tests with no remaining finding. A final localized question-copy adjustment passed 86 interpreter/recovery tests. The complete workspace suite was not repeated after these focused checks.
- Bounded live browser proof: `عندي جيبة بني في بيج و عايزة بلوزة تلي عليها` returned the two verified shirts. `افتح صفحة القميص الرسمي` then completed and opened the Storefront's Formal Shirt page at `/p/clothing-05`. The running provider was used for both turns; no key limit was changed.
- All demo services were restarted after isolated automated testing. Credentials and raw diagnostic captures remain ignored. Ticket 14 and broad refactors were not included.
