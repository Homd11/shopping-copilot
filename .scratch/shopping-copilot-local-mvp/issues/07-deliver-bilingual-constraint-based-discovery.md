# 07 — Deliver bilingual constraint-based discovery

**What to build:** Let Shoppers find deterministic products using Egyptian Arabic, English, Franco-Arabic, mixed input, normalized Constraints, and the Controlled Storefront's configured EGP currency.

**Blocked by:** 04 — Evaluate the first complete browser flow.

**Status:** resolved

- [x] The Controlled Storefront contains roughly sixty fictional products across four categories with Arabic and English names and varied attributes.
- [x] The Storefront Definition supplies bilingual vocabulary, filter capabilities, URL rules, and an ISO currency code fixed to EGP for the MVP.
- [x] Missing or malformed currency configuration fails clearly at startup rather than being guessed.
- [x] Arabic-Indic and Latin digits, common separators, and EGP wording normalize to exact decimal Money values.
- [x] Requests in another currency ask for an EGP amount without conversion or silent reinterpretation.
- [x] Category, type, price, size, color, availability, search, and sorting behave deterministically.
- [x] Valid zero-result searches remain empty and offer to relax one named Constraint without silently broadening results.
- [x] Fully understood filters use one direct same-origin navigation when supported and fall back to visible controls when the expected state is absent.
- [x] Evaluation Cases cover Arabic, English, Franco-Arabic, mixed-language, ambiguous, unavailable, and empty-result scenarios.

## Comments

- Added the EGP-only Storefront Definition, exact Money normalization, a 60-product bilingual catalogue, deterministic filtering, and constraint-aware empty states.
- Seven real-browser Evaluation Cases now cover the required language and result-state variants.
