# Groq minute-limit repair

The owner could not run the Agent after replacing the key. A direct, single-attempt diagnostic captured HTTP 429 with TPM limit 8000, used 4299, requested 4690, and Retry-After 8 seconds. This establishes a minute-token limit, not exhaustion of the 200000-token daily allowance. Another successful diagnostic response reported 4315 input tokens and 424 completion tokens. No credential or organization identifier is retained here.

## Repair

The Groq adapter now pauses on 429, retains a monotonic client cooldown, and prevents early manual retries from sending another HTTP request. The pause message includes the remaining wait time. Missing/invalid Retry-After uses a conservative 60-second fallback. Invalid structured output no longer causes an automatic second paid request; existing explicit Retry/Stop behavior remains.

Request JSON is compacted and non-validating schema annotations are removed; constraints, required fields, strict schema behavior and validation remain intact. No exact token-reduction claim is made without post-change usage evidence.

The diagnostic also reproduced an invalid interpretation of the owner's written `اتنين كمان` request. Prompt intent-v14 gives the explicit relative-quantity example with verbatim evidence, and current-message number evidence now recognizes basic written English/Arabic quantities. No automatic mutation replay or provider fallback was added.

## Standards

Independent bounded review found no actionable safety or correctness finding. Cooldown regression uses a mock transport and clock, asserting no HTTP call before expiry and a new call after expiry. Provider details are not exposed in the new exception.

## Spec

Independent bounded review found no behavioral mismatch. Its test-field typo observation was corrected (`pause_message` rather than nonexistent `summary`). Tests cover the visible wait time and absence of an Action while paused.

Review findings remaining: Standards 0; Spec 0. Final verification and live manual acceptance are recorded in the newest checkpoint.

Final verification: 137 TypeScript + 333 Python tests passed. The exact Arabic request passed through the live Groq browser path, changing only Playmaker 1 to 3; Cairo Jacket stayed 1. The cart was restored after acceptance.
