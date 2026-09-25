# Manual cart acceptance repair

The owner reproduced selected-product add handback, a relative-quantity request in a multi-item cart, and a non-working manual empty-cart control. The Agent was restarted to load the updated local API key; no credential was printed or committed.

## Reproduced causes and repairs

- A live Groq response for `ضيفلي المنتجده للسلة` returned missing query despite the selected product page. Cart planning now resolves current-item/query/variant omissions through unambiguous visible controls while retaining conflicting/ambiguous handback.
- Arabic color evidence such as `اللون اسود` was compared literally with canonical `black`. Validation now uses the trusted Storefront vocabulary. A later live response dropped explicit variants entirely; explicit size markers and color-selection clauses recover them from the current request, while conflicting values fail closed. Owned-item color mentions do not override current selections.
- Quantity intents lacked a relative/absolute distinction. Schema v6 and prompt intent-v13 introduce explicit set/increase/decrease, validate recognized direction against current request evidence, and compute the target quantity from the matched visible line. Grouped line controls distinguish products/variants. Ambiguous lines hand back without an edit.
- The manual empty-cart button posted an empty Confirmation token. A native dialog now presents the bulk-clear effect, supports Cancel, and registers one revision-bound token only after a trusted manual confirmation click. The existing guarded form/server enforcement remains in place. Ordinary Bridge clicks cannot authorize this path, and a changed cart invalidates the confirmation.

## Standards

The independent review identified a remaining relative-quantity contradiction (increase/decrease by N could become set N). Fixed with required v6 quantity mode and direction regressions; recheck found no remaining issue in this repair.

## Spec

The independent review identified the same quantity gap and over-broad color recovery that could use an owned item's color. Both were fixed and rechecked. A regression preserves selected options for `I own black shoes; add this to my cart`.

Findings: Standards 1 resolved; Spec 2 resolved. Architecture refactors remain deferred.

## Evidence

Red-to-green Agent tests cover current-page resolution, Arabic aliases, dropped explicit variants, named relative quantity, contradictory/omitted modes, and preservation of owned-item context. Browser tests cover named +2 in a two-product cart with exact Undo; manual clear confirmation/cancel; stale-cart refusal; and a blocked ordinary Bridge click on the confirm control. Full verification results are recorded in the newest project checkpoint.

Live provider probes remain bounded: an initial missing-query response and a later v6 add response were observed, with intervening provider errors. Deterministic browser success is not a claim of live-provider availability or end-to-end reliability. The owner's cart lines were saved locally for restoration after isolated tests.
