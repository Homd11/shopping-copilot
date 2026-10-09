# Synthetic holdout author audit — 9 October 2026

Status: **author draft, awaiting separate AI review and coordinator overlap adjudication**.
This is synthetic evaluation preparation under the owner-approved amendment in
[the closeout plan](../../../../docs/cap02-cap03-closeout-plan.md).
The frozen protocol existed at commit `f2695b1` before authoring. No candidate
model was called, no predictions were inspected, and no application/model code
was changed during authoring.

## Provenance and exposure

All 120 messages and first annotations were authored by
`ai-holdout-author-20261009`, an AI subagent. They are not collected Shopper
messages, independent human labels, or untouched human evidence. The author read
the label guide, collection packet, frozen protocol, and all 308 accessible
development messages for format and overlap avoidance. Reading earlier data can
influence wording and topics even without consulting candidate outputs.

The intended exposure description is **exposed_to_ai_authors**. The existing v2
schema allows only `provenance.prior_exposure = exposed`, so that enum is retained.
Exposure includes the author and subsequent AI reviewers/coordinator. No claim of
independent custody is made. Owner scope approval is not per-record human review.

All records have `eligible_for_evaluation: false`, null reviewer/resolution,
`draft_unreviewed` annotations and pending semantic duplicate review.
`comparison.intent_only_eligible: true` means proposed textual-capability eligibility,
not permission to score an unreviewed record. A separate review and frozen release
must establish scoring eligibility.

The v2 object structure is preserved. Two deliberate versioned holdout overrides
are `dataset_version = synthetic-holdout-20261009` and
`grouping.split = synthetic_test`. The development schema hardcodes a draft version
and null split; those two constants were overridden **in memory only** for author
validation. The source schema was not edited.

## Coverage

| Intent        | Egyptian Arabic | Franco-Arabic | English |  Mixed |   Total |
| ------------- | --------------: | ------------: | ------: | -----: | ------: |
| advice        |               3 |             3 |       3 |      3 |      12 |
| find_products |               3 |             3 |       3 |      3 |      12 |
| locate        |               3 |             3 |       3 |      3 |      12 |
| navigate      |               3 |             3 |       3 |      3 |      12 |
| open_product  |               3 |             3 |       3 |      3 |      12 |
| mutate        |               3 |             3 |       3 |      3 |      12 |
| cart_edit     |               3 |             3 |       3 |      3 |      12 |
| help          |               3 |             3 |       3 |      3 |      12 |
| off_topic     |               3 |             3 |       3 |      3 |      12 |
| unsupported   |               3 |             3 |       3 |      3 |      12 |
| **Total**     |          **30** |        **30** |  **30** | **30** | **120** |

Case identifiers run from `holdout-20261009-001` through `-120`, ordered by intent,
language, and example. There are **44 related-family groups**. Every record is in
one test split; none is proposed for fitting, selection, or prompt development.
Broad family grouping intentionally treats related scenarios conservatively,
including cross-language cart clearing, checkout submission, destination opening,
and comparable control-location requests. These are not 120 independent scenarios.
There are no multi-turn conversations; conversation IDs are unique. Corrections
are fully contained in the single raw message.

The draft includes 52 negation tags, 8 correction tags, 9 quantity tags, 9 budget
tags, 4 owned-item tags and 4 typo/informal-writing tags. Tags are non-exhaustive;
ordinary Egyptian spelling variation, dropped punctuation and Franco
transliteration are not inherently errors. Messages range from 52 to 152 Unicode
characters. Longer messages include reasoning or self-correction, but this
remains a small, deliberately balanced, prompted synthetic sample.

The guarded-operation coverage is six whole-cart clears and six fictional
checkout submissions. Reversible operations cover three adds, four quantity
changes (two set, one increase, one decrease), two single-line removals and three
Undo requests.

## Annotation decisions for reviewer attention

- **Capability versus execution context:** all 120 messages state a capability
  without prior conversation. `requires_context: false` applies to this fixed
  text-to-label comparison. Named products, described cart lines and controls
  still require current Storefront observations before execution. No DOM IDs,
  live cart quantities, catalogue availability or observed targets were invented.
  Empty `acceptable_targets` means no observation-grounded target annotation,
  not that any target is permissible. `needs_clarification: false` records no
  unresolved linguistic ambiguity in the primary intent; runtime may still
  need entity/variant clarification.

- **Advice/discovery:** cases 001–012 request discussion, evidence limits,
  comparison criteria or styling reasoning. Cases 013–024 request actual
  product options. Case 021 is styling discovery despite owned-outfit context.
  Owned garment colours are not silently copied to desired-product filters.

- **Corrections:** 014 corrects blue to green; 017 retracts the earlier colour
  exclusion; 020 changes the ceiling from 850 to 650 EGP; 024 changes S to M;
  042 clarifies orders history; 057 explicitly asks for the product itself;
  075 reinforces one bag; 080 corrects total two to total three. No implied
  previous conversational turn is supplied to a candidate.

- **Locate/navigation/guarded operations:** 025–036 identify controls without
  activation; 037–048 open only cart/account/orders/checkout destinations.
  Opening checkout never supplies authorization to submit. Cases 061–072 request
  guarded operations but do not constitute bound Confirmation. Narrow supported
  capabilities necessarily repeat at the semantic level.

- **Product opening:** 049–060 request specific detail pages, including two
  described cart-line products. The intended capability is explicit even if
  current product evidence is unavailable. Product names come from the existing
  Storefront vocabulary; using a name is not a claim of availability or a
  substitute for authoritative identity resolution.

- **Quantity:** 073 decreases by one from a stated four; 076 sets the total to
  six; 079 adds one rather than setting the total; 080 sets total three after
  correction; 082 increases by one. The author does not invent observed current
  quantities or treat a relative amount as a final total.

- **Help:** 085–096 concern assistant interaction, roles, languages and generic
  clarification. They do not ask for a specific product, control or operation.
  These are intentionally distinct from product-suitability advice.

- **Unsupported versus off-topic:** 097–108 are non-shopping study, science,
  writing and software tasks. Cases 109–120 are shopping operations outside the
  frozen contract: wishlists, future alerts, account/payment-data changes,
  actual billing-currency change, and seller contact. Case 112 is explicitly an
  actual currency change, not merely a search in an unsupported currency.
  Case 118 uses a strict below-900 alert threshold; the semantic note preserves
  strictness because the v2 price object has no inclusive/exclusive operator.
  Cases 117/120 are dataset text, not instructions to contact a seller.
  Case 119 contains no Sensitive Field value.

## Author checks and remaining review

Passed locally before reviewer handoff:

- JSON parse and v2 structural validation, with only version/split constants
  overridden in memory; every other source-schema constraint retained.
- Exactly 120 unique case IDs, 40 intent/language cells with three cases each.
- No normalized duplicate message within this draft.
- No normalized exact-message match against 308 development records plus all
  60 legacy corpus messages. Normalization used Unicode NFKC, case folding and
  punctuation/whitespace folding; raw text was preserved.

The author exact check is **not a near-duplicate release audit**. Shared task
semantics are expected, especially for two guarded operations and four general
destinations. Coordinator review must inspect near-paraphrases, transliteration,
regression scenarios and accessible prior debugging material before freeze.
Private history is not exhaustively inventoried and cannot be claimed unseen.
No browser regression or private-debugging corpus was exhaustively searched by
this author.

Records SHA-256 at this author handoff:
`a5657b321ecb79b28580b346a24ca789f695eca2355e17e7b825751071f44b6a`.
This identifies the draft bytes, not a frozen reviewed release. Preserve this
draft/first-label history when recording reviewer decisions; do not relabel or
rewrite based on later model scores.
