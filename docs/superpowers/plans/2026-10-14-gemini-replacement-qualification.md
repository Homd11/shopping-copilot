# Gemini replacement qualification plan

Date: 14 October 2026. Owner approved qualification before CAP-04 ticket 05.

## Frozen protocol before calls

Candidate: OpenRouter `google/gemini-3.5-flash-lite`. Existing reference:
`google/gemini-2.5-flash`. Public models API reports reference expiration
2026-10-20; candidate expiration is null. Google Gemini API's own lifecycle page
lists no 2.5 Flash shutdown, while its Cloud/Vertex schedule lists 20 October.
OpenRouter's route-specific expiration governs this migration decision.

Prices checked from OpenRouter's public registry: candidate and reference
$0.30/M input, $2.50/M output. Candidate supports reasoning, response_format and
structured_outputs. Gemini 3.1 Flash-Lite is cheaper ($0.25/$1.50) but not the newest
recommended Lite; Gemini 3.8 Flash is $0.75/$3.75 and would expand per-call costs.
Use the equal-price candidate first. No inference run on those other models is
part of this protocol. Sources: https://openrouter.ai/api/v1/models,
https://openrouter.ai/google/gemini-3.5-flash-lite,
https://ai.google.dev/gemini-api/docs/deprecations.

- Keep prompts, wire schemas, interpretation and safety guards unchanged.
- Extend the explicit allowed-model set only to the candidate and current reference;
  no automatic model fallback. Reasoning remains disabled, existing output bounds,
  schema translation, parameter requirements and price filters remain intact.
- Offline adapter tests must observe the candidate reaching the payload with
  unchanged restrictions; unsupported models remain rejected.
- Qualification-only request transport reserves from the actual POST payload,
  caps all new qualification usage at $0.25 and all model POSTs at 120. Keep unknown
  charges reserved; read-only key checks are free. The existing total key limit
  stays $2, reset Never. Persist per-attempt evidence; never resume an allowance
  after restarting the qualification process with an empty record.
- Run the existing complete 44-case browser milestone gate once with the candidate.
  Require its unchanged >=40/44 overall, all 19 designated safety cases, complete
  measurements and existing latency/efficiency thresholds. This is a replacement
  qualification, not a rerun/alteration of historical Ticket 15 evidence.
- Run additional messy advice/follow-up conversations with verified catalogue
  references, explicit read-only cart assertions and trade-off/unknown-fact checks.
  Require all selected supplemental cases to pass before switching.
- Record cost, latency, failures and raw local report paths. No tuning the model or
  prompts on these failures to silently turn them into initial-pass evidence.
- Only after acceptance: update the owner's local .env model ID (no keys printed),
  documentation and rollback instructions; runtime budget and output bounds stay.
- Run relevant full offline suite/build/typecheck/lint/format once after code changes,
  obtain independent reviews, commit local changes, then proceed to ticket 05.

The reference remains configured until acceptance. Budget exhaustion or candidate
failure keeps migration open, with failure evidence retained. No cap increase,
purchase, DNS/AWS resource change or new baseline model score is authorized.

## Diagnostic and approved second-set amendment

The first set retained 18 HTTP-rejected POST reservations ($0.2462835); the
provider's reported key usage was unchanged. It did not qualify the candidate.
The owner explicitly authorized one diagnostic and one new set, together capped
at an additional $0.25 within the unchanged $2 total key cap.

The diagnostic returned HTTP 400: reasoning is mandatory and cannot be disabled.
The public registry lists mandatory reasoning and supports minimal effort.
Candidate-only configuration therefore uses `effort: minimal`, `exclude: true`;
the reference still disables reasoning. Prices, prompts, schemas and output bounds
remain unchanged. The diagnostic retains $0.0096027, so the second set receives
at most $0.2403973/119 POSTs. A separate fixed exclusive claim prevents relaunch.
This operational decision was communicated before the second set; this written
amendment was added after it began, not retroactively represented as pre-registered.

The second set passed three cases before a telemetry ECONNRESET interrupted it.
Five completed model POSTs recorded $0.0064956, no unsettled reservations. This is
incomplete evidence and does not authorize switching the configured model.
Neither failed set nor its allowance is silently erased or renewed.

## Final verification revision — 15 October

The owner explicitly reprioritized completing the replacement: retaining the
retiring reference is not an acceptable final outcome. The full resumed set had
42/44 core passes, a failed reconnect fixture, and 5/6 advice cases. Retain that
failed cohort; do not promote rechecks into its initial score. Its no-match answer
for black/44/under2000 was correct: shoe-01 offers 40/41/42, not44.

An offline public-seam regression reproduced a general validation defect: owned
garment types/colours and soft preferences were constrained to store vocabulary.
Read-only advice/discovery now lets catalogue evidence establish verified, unmet
or unknown facts. Known product IDs, currency, Action capabilities and cart guards
remain enforced. One shared discovery predicate keeps execution and validation
consistent. The reconnect fixture omitted credentials CORS; scripted browser
reproduction and repair do not count as model-language evidence.

Run one fresh full 44-case verification plus original supplemental advice and one
actual exact-match explanation (black/42/under2000). Use the SAME durable allowance,
retaining every prior charge, not a new $0.25 allocation. The initial diagnostic's
$0.0096027 stays separately reserved; the ledger's total remains $0.2403973.
Allow at most120 further POSTs, with a fixed global200-POST ceiling. This extends
the earlier call-count protocol to complete the owner's mandatory replacement;
it does not expand the approved cumulative dollar amount or the $2 key cap.
Use a new exclusive final marker and source manifest; preserve prior reports.
Require unchanged core thresholds/all19 safety cases, all advice checks and manual
catalogue-fact review before switching. No prompt tuning or phrase rules.

## Owner-approved post-fix set — 15 October

The previous final cohort retained 42/44 core passes, all19 safety passes and all7
advice checks. It failed filter efficiency: one request entered catalogue advice,
and another copied an English type phrase into literal product-name search. The
first behavior varied on repeat; the second reproduced. Both targeted live checks
pass after reviewed `intent-v32` prompt/schema descriptions distinguish canonical
filters from literal query and explicitly preserve additional facts/exclusions.
No runtime phrase rules or safety changes implement this correction. This is a
disclosed amendment to the original no-prompt-change protocol, not an initial pass.

The owner explicitly approved **one additional full set, maximum $0.12**, inside
the unchanged $2 total non-resetting key limit. Use an exclusive approved-4 claim,
fresh source manifest and at most120 POSTs; no automatic continuation, refill or
threshold changes. Retain every prior report/charge separately. Require the same
44-case core gate, original six advice cases, actual exact-match explanation and
manual catalogue review. Switch only on acceptance for this reviewed prompt.
