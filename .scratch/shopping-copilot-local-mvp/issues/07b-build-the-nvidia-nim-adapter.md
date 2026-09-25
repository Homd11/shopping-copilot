# 07B — Build the NVIDIA NIM adapter

**What to build:** Connect the Agent to NVIDIA's OpenAI-compatible hosted NIM endpoint through the provider-neutral model boundary, without exposing credentials or making ordinary tests depend on the network.

**Blocked by:** 07A — Define the provider-neutral LLM contract.

**Status:** resolved

- [x] The adapter calls NVIDIA from the Python Agent only and reads its API key exclusively from local environment configuration.
- [x] The configured endpoint and model identifier are explicit and recorded with every model call.
- [x] Requests use a configurable timeout that defaults to twenty seconds for development.
- [x] Transient network failures, throttling, and invalid structured output receive at most one retry with short exponential backoff and jitter.
- [x] Partial, timed-out, or invalid responses can never emit a browser Action.
- [x] Usage metadata records latency, tokens when reported, model identifier, parameters, prompt version, schema version, and failure category without recording the credential.
- [x] Mocked adapter tests cover successful output, timeout, throttling, malformed output, retry exhaustion, and secret-safe logs.
- [x] Real-provider smoke tests require an explicit opt-in flag and never run in ordinary test or CI commands.

## Comments

- The credential pasted into chat is considered compromised and must not be used or stored. A rotated replacement belongs only in the developer's ignored local `.env`.
