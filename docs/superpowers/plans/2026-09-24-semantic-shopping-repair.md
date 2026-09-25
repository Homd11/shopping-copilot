# Semantic shopping repair

Approved scope: repair the current 07E/08 experience, not add a database, checkout mutations, AWS, or a new storefront. Preserve existing local changes. Work directly in the owner's local checkout because the working implementation is uncommitted here.

## Contract and global constraints

- Structured Intent v3 adds `request_mode` (`browse`, `recommend`, `style`), `owned_items` (up to six OwnedItem values), `preferred_colors` (up to six canonical colours, soft styling opinions), and `navigation_source` (an exact shopper span). Legacy v1/v2 intents remain readable.
- Existing `owned_item` remains a compatibility field. `desired_wear_position` supports upper/lower/footwear. Owned items are context, never constraints on the requested product.
- Canonical vocabulary and literal source spans constrain LLM output; semantic paraphrase understanding belongs to the LLM, not an exhaustive verb dictionary. Source presence does not prove semantic correctness; held-out live checks remain necessary.
- Explicit requirements, EGP, catalogue facts, origin/action/confirmation/login/lease/staleness protections remain deterministic. Style preferences are opinions, never invented product facts or mandatory colour filters.
- Retain a bounded clarification context, not a full conversation or browser Snapshot. Merge preserved intent before catalogue routing and validation. A new independent request does not inherit old outfit constraints.
- An explicit clarification correction can name `revised_fields` with a current `revision_source` span; removed constraints stay removed rather than being restored from context. Catalogue revisions replace the retained requirements with the model's complete remaining list.
- Show at most three catalogue-verified options for recommendation/style requests. Respect requested size/type/budget/use cases; clearly label near matches and unmet requirements. Never describe an unavailable or unverified attribute as a match.

## Tasks

1. Root: schema v3, source-anchored semantic interpretation, owned/requested separation, canonical vocabulary, routing and focused regressions.
2. Implementer: bounded clarification context in SessionStore, and general catalogue styling selection replacing the black-trousers special case. Tests at those public seams. Own sessions.py, catalogue.py and new/associated tests; no intent_pipeline.py/app.py edits.
3. Root: integration, safety/browser regressions, paced live Groq acceptance including the owner's outfit request and original three requests; docs and manual handoff.
4. Independent final review of the repair, then required fixes and verification.

## Progress / decisions

- Diagnosis: category clarification replaced the original request with `Shoes`; resolved_state retained only filters. Styling evaluator accepted only black trousers plus upper-body clothing.
- Interface review: tasks 1/2 share StructuredIntent. Task 1 owns schema; Task 2 consumes the fields above. Session context must be merged before root catalogue routing, not just during final planning.
- Ruling: retain local dirty checkout and do not commit unrelated work; review uses scoped files and tests rather than a misleading HEAD-only diff.
- Ruling: one intent call with soft palette suggestions is sufficient for this repair; a second ranking model and large-catalogue retrieval are deferred. Tradeoff: ranking remains modest, but product claims remain verifiable.
- Task 1 implemented: v3 schema, semantic source anchoring, requested/owned separation, correction-aware context merge, app catalogue routing, and focused regressions. Live intent probe recognized the owner's green/brown outfit without a category question.
- Task 2 implemented: worker report `2026-09-24-semantic-repair-worker-report.md`; bounded context, one-use prior destination, generic style evaluator and truthful summary labels. Root API test confirms clarification-to-suggestions flow.
- Task 3: seven-case live browser run passed (`eval/reports/semantic-repair-browser-20260924T194201Z.json`): both outfit cases, novel account wording, original black-trousers case, and all three unchanged owner requests.
- Review corrections addressed: field-specific revision coverage, explicit browse/reset/replacement of owned context, narrow owned-item spans (including overlapping type aliases), and colour-free explanations for unknown colours. Real-model response schema requires v3; a model-declined v3 request is not promoted to navigation by legacy verb rules. Root finished the final small correction when the worker hit its usage limit.
- A final live deictic followup initially asked again for its destination. Making the previous verified destination explicit in the prompt, with a generic English referential example rather than an Arabic phrase rule, resolved the replay. `eval/reports/semantic-followup-browser-20260924T195250Z.json` passed locate → natural-language open followup → sign-in wait without repetition → shopper authentication → completion. The earlier failed report remains recorded, not counted as a pass.
- Final regression/owner replay evidence and manual service readiness are recorded in `PROJECT_CHECKPOINT.md`.
