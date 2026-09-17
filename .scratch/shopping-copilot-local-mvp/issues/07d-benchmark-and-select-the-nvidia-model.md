# 07D — Benchmark and select the NVIDIA model

**What to build:** Select a pinned NVIDIA-accessible model using this project's language, schema, safety, latency, and cost evidence rather than reputation.

**Blocked by:** 07C — Build the multilingual intent pipeline.

**Status:** ready-for-agent

- [ ] A versioned corpus contains at least sixty Egyptian Arabic, English, Franco-Arabic, mixed-language, ambiguous, unsupported-currency, malformed-budget, off-topic, and adversarial cases.
- [ ] Two or three accessible candidate models run against identical prompt, schema, parameters, and corpus versions.
- [ ] Results report schema validity, exact intent-and-Constraint accuracy, clarification accuracy, safety outcomes, latency, token usage, and estimated cost.
- [ ] A candidate passes only with 100% schema validity, currency and safety compliance, and destructive-ambiguity clarification, plus at least 95% overall exact intent-and-Constraint accuracy.
- [ ] Critical safety and language cases repeat three times at the lowest deterministic settings the provider supports.
- [ ] Accuracy wins over speed within the twenty-second development timeout; a smaller model is accepted only if it passes the same gate.
- [ ] The winning exact model identifier and all reproducibility metadata are pinned in configuration and the evaluation report.

## Comments

- Normal CI continues using the scripted model double. This benchmark is an explicit, credentialed evaluation run.
