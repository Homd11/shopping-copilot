# 07 — Deliver bilingual constraint-based discovery

**What to build:** Let Shoppers find deterministic products using Egyptian Arabic, English, Franco-Arabic, mixed input, normalized Constraints, and the Controlled Storefront's configured EGP currency.

**Blocked by:** 04 — Evaluate the first complete browser flow.

**Status:** ready-for-agent

- [ ] The Controlled Storefront contains roughly sixty fictional products across four categories with Arabic and English names and varied attributes.
- [ ] The Storefront Definition supplies bilingual vocabulary, filter capabilities, URL rules, and an ISO currency code fixed to EGP for the MVP.
- [ ] Missing or malformed currency configuration fails clearly at startup rather than being guessed.
- [ ] Arabic-Indic and Latin digits, common separators, and EGP wording normalize to exact decimal Money values.
- [ ] Requests in another currency ask for an EGP amount without conversion or silent reinterpretation.
- [ ] Category, type, price, size, color, availability, search, and sorting behave deterministically.
- [ ] Valid zero-result searches remain empty and offer to relax one named Constraint without silently broadening results.
- [ ] Fully understood filters use one direct same-origin navigation when supported and fall back to visible controls when the expected state is absent.
- [ ] Evaluation Cases cover Arabic, English, Franco-Arabic, mixed-language, ambiguous, unavailable, and empty-result scenarios.
