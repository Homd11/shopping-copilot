# LLM interpretation and runtime validation

Approved by the project owner on 26 September 2026 after the [hardcoding audit](hardcoding-audit-2026-09-26.md). Ticket 14 remains on hold until this repair is manually accepted.

## Responsibility

The LLM owns natural-language meaning: typos, Egyptian Arabic, Franco-Arabic, negation, quantities and their direction, references, owned outfit context, soft preferences, and clarification. Runtime code must not match shopper words to verb lists, number dictionaries, product aliases or negation patterns to approve or rewrite its meaning.

Runtime checks still verify schema, supported capabilities and catalogue property kinds, currency and numeric bounds, observed target IDs/roles/options, freshness, same origin, sensitive-field exclusion, duplicate rejection and bound confirmation. Canonical capability membership is not a shopper-language dictionary: for example, a material cannot be misclassified as a use case to bypass an exclusion.

Live interpretation requires schema 8. Earlier versions remain readable for persisted state and explicit scripted tests; a live provider cannot select those legacy execution paths. The legacy `/step` endpoint is unavailable outside scripted configuration. Ordinary scripted browser tests remain explicit execution fixtures; they are not language acceptance tests.

## Current observations and targeting

The model receives the current semantic Snapshot with visible non-sensitive elements, target IDs, names, groups, allowed form actions, product options/selections and cart quantities. Arbitrary textbox values and Sensitive Fields are excluded. A decision is rejected if the session's Snapshot changes while the model is working.

For a cart operation the model selects an observed button ID, not a name for another parser to resolve. Quantity arithmetic uses the observed current value plus/minus the model's delta. For quantity/removal requests outside the cart, the agent first navigates to the cart, then interprets the original request against that fresh Snapshot. Duplicate delivery of that navigation result does not launch another interpretation. Model clarification remains a question, even if its redundant missing-field label is absent.

Current controlled-store execution still knows form routes and accessible control labels. These are store adapter assumptions, not shopper-language interpretation. General storefront navigation, ranking redesign and free-form recommendation prose are outside this repair.

## Exclusions

Catalogue requirements carry `excluded: true` for forbidden properties. Known products with that property are excluded from suggestions. A positive-only product fact list cannot prove the absence of a material: products whose material is unverified may appear only as labeled alternatives with that gap disclosed, never as verified non-leather matches. Unsupported property/kind combinations cannot reach catalogue evaluation.

## Evidence and evaluation

Run the opt-in real-provider cases with `LLM_LIVE_EVAL=1 python -m eval.semantic_boundary_live`. The runner refuses scripted configuration, caps itself at 14 provider calls per run, preserves the existing provider spending cap, and writes model drafts, validated intent and planned actions under ignored `eval/reports/`. Set `LLM_EVAL_CASE` to rerun one named case. Actual browser execution uses `LLM_BROWSER_SMOKE=1 python -m eval.openrouter_cart_browser`; `LLM_BROWSER_CASE` selects add, quantity, remove or clear without repeating the other paid cases. These fixtures define observed pages and expected outcomes; they do not provide model answers.

The initial ten-case live run passed nine cases. The model correctly requested clarification for two shirt variants, but schema validation rejected its missing-field omission. After allowing that safe question, the focused ambiguity rerun passed. Tested cases include quantity wording and a typo, set versus increase, multiple variants, a negated edit, removal, bulk clear, `مش جلد`, written budgets and a prompt-override request. This is a small sample, not universal language reliability.

The runtime tests cover observed/wrong-role target IDs, fresh-cart interpretation, exact selected-line updates, duplicate results, safe clarification, source privacy, schema downgrade rejection, unsupported catalogue properties and scripted endpoint isolation. Existing confirmation, execution, origin and recovery checks remain. Obsolete tests that expected validators to understand or repair sentences were retired; they must not be restored as keyword gates.

Independent Spec and Standards reviewers identified and verified fixes for canonical capability membership, live schema downgrade and the scripted endpoint. Full workspace results and manual acceptance status are recorded in PROJECT_CHECKPOINT.md.

The actual two-product browser run passed quantity, removal and confirmed clearing. Add initially exposed a representation mismatch: the model used `set` for the product form quantity. Schema 8 now permits that explicit representation, defining it as units to add, while rejecting add/increase and add/decrease. A focused live add rerun passed with exact Undo restoration. The final change passed independent review and focused regression checks. Services were restarted and the saved cart restored; owner manual acceptance is still pending.
