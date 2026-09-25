# 07D — Benchmark and select the local intent model

**What to build:** Select a pinned provider/model pair using this project's language, schema, safety, latency, and cost evidence rather than reputation.

**Blocked by:** 07C — Build the multilingual intent pipeline.

**Status:** resolved

- [x] A versioned corpus contains at least sixty Egyptian Arabic, English, Franco-Arabic, mixed-language, ambiguous, unsupported-currency, malformed-budget, off-topic, and adversarial cases.
- [x] Two or three accessible candidate models run against identical prompt, schema, parameters, and corpus versions.
- [x] Results report schema validity, exact intent-and-Constraint accuracy, clarification accuracy, safety outcomes, latency, token usage, and estimated cost.
- [x] The strict 100% schema/currency/safety and 95% exactness gate remains recorded and is explicitly deferred to the final AWS Bedrock migration rather than represented as passed locally.
- [x] Critical safety and language cases repeat three times at the lowest deterministic settings the provider supports.
- [x] The local baseline decision records the observed accuracy, safety, and latency evidence; it does not conceal the candidate's gate miss.
- [x] Groq `openai/gpt-oss-120b` with low reasoning effort is pinned in local configuration under an explicit development waiver.

## Comments

- Normal CI continues using the scripted model double. This benchmark is an explicit, credentialed evaluation run.
- The original candidates and two initially approved replacements reached provider end of life during implementation. Live probe results selected the current evaluation set: `nvidia/nemotron-3.5-lightning-30b-a3b`, `nvidia/nemotron-3-super-120b-a12b`, and `nvidia/nemotron-3-ultra-550b-a55b`.
- Benchmark run `intent-benchmark-20260917T185654Z.json` failed the selection gate for every candidate. No model is pinned. The next work must improve the prompt/evaluation evidence or introduce a newly approved candidate; proceeding to real Shopping Task integration would violate the model-selection gate.
- Prompt v2 and the diagnostic rerun `intent-benchmark-20260918T021838Z.json` improved Super and Ultra but neither reached the gate. Category diagnostics isolate failures in Franco/mixed language, unsupported or malformed budgets, and some off-topic/adversarial cases. No model is pinned.
- Prompt v3 with deterministic foreign-currency and malformed-budget enforcement produced `intent-benchmark-20260918T023532Z.json`. Super improved to 55/104 exact results and 33/66 critical-safety passes; Ultra regressed to 42/104 and 12/66 respectively. Neither passed. The run exposed that enforcement occurs after provider response validation; the next implementation change must return a deterministic safe clarification when a flagged budget message cannot produce a valid model response. No model is pinned.
- Pipeline v4 adds that deterministic safe clarification fallback, blocks such clarification states from browser actions, and reports redacted failure categories. In `intent-benchmark-20260918T024547Z.json`, Super produced 54/104 exact results, 31/66 exact critical-safety results, and six HTTP-status failures; Ultra produced 10/104 exact results and 93 HTTP-status failures. Neither is eligible, no model is pinned, and ticket 07E remains blocked pending a provider/model decision.
- Post-benchmark NVIDIA viability probes did not yield a replacement. The live catalog no longer includes the suggested `meta/llama-3.3-70b-instruct`; both `nvidia/llama-3.1-nemotron-70b-instruct` and `nvidia/llama3-chatqa-1.5-70b` returned HTTP 404 from the chat-completions endpoint. Per the approved fallback, move to external-provider evaluation rather than retrying Ultra or pinning an unproven NVIDIA model.
- Groq is the approved next provider and `qwen/qwen3.8-27b` is the first candidate. The provider-neutral benchmark switch and model list now work for any configured real adapter; Groq strict-schema rules remain private to its adapter.
- Architecture review kept the public `LLMClient` and `LLMRequest` interfaces unchanged, made the benchmark opt-in and candidate configuration provider-neutral, and split critical-safety scoring from exact intent accuracy. The Groq key remains local and was validated only through redacted metadata and live intent outcomes.
- Groq live viability rejected both free-tier candidates under the original strict gate without spending quota on the full repeated benchmark. `qwen/qwen3.8-27b` scored 7/9 exact despite 9/9 schema and safety, with repeated invention of unstated Constraints. `openai/gpt-oss-120b` scored 8/9 exact on the first sample, then 12/18 exact and 17/18 safe on eighteen additional unseen cases; it followed an Arabic injected checkout instruction.
- The unsafe Groq result exposed a provider-independent invariant: navigation/locate authority cannot coexist with product-discovery Constraints, and discovery intent cannot carry a navigation target. Structured Intent now rejects that combination deterministically before planning.
- The Intent Boundary additionally detects the approved Arabic/English prompt-override pattern and prevents it from authorizing navigation even if a model returns a pure navigation result. This is covered by a deterministic regression test.
- On 2026-09-18 the owner explicitly accepted Groq `openai/gpt-oss-120b` with low reasoning as the local MVP baseline to avoid premature AWS credit use. This resolves 07D and unblocks 07E under a documented waiver; it does not claim the model passed the original strict gate. Strict re-benchmarking is required during the final Bedrock migration.
