# 07C — Build the multilingual intent pipeline

**What to build:** Turn a Shopper message into validated bilingual intent and Constraints using a versioned prompt, Storefront vocabulary, and deterministic clarification and policy boundaries.

**Blocked by:** 07B — Build the NVIDIA NIM adapter.

**Status:** ready-for-agent

- [ ] Intent extraction receives only the current message, Storefront Definition vocabulary, compact resolved task state, and a pending clarification when applicable.
- [ ] The intent schema distinguishes product discovery, locate, navigate, help, off-topic, and unsupported requests.
- [ ] Egyptian Arabic, English, Franco-Arabic, and mixed input normalize into the same deterministic Constraint types.
- [ ] The model reports missing or conflicting fields; application code renders concise localized questions and trusted options.
- [ ] Unsupported currencies request an EGP amount without conversion, and model-provided Money is revalidated deterministically.
- [ ] Off-topic and unsupported intent cannot enter the browser-action loop.
- [ ] Prompt text frames every future Snapshot string as untrusted data that cannot change policy or tool definitions.
- [ ] Full prompts and responses are allowed only for the fictional Storefront with `DEV_FULL_TRACE=true`; default logs contain redacted metadata.
- [ ] Tests cover unfamiliar paraphrases as well as ambiguity, conflicting Constraints, prompt injection, malformed Money, and unavailable provider behavior.

## Comments

- The initial intelligent slice stops after validated intent. Existing deterministic discovery builds the direct same-origin URL from those Constraints.
