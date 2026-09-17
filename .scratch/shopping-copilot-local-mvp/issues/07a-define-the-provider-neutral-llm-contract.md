# 07A — Define the provider-neutral LLM contract

**What to build:** Introduce the narrow Agent-side model boundary, configuration, structured intent types, and deterministic test double needed to use real providers without moving policy into the model.

**Blocked by:** 07 — Deliver bilingual constraint-based discovery.

**Status:** resolved

- [x] `LLMClient` exposes an async, stream-capable provider-neutral interface while structured intent calls wait for one complete validated result.
- [x] Provider configuration requires an explicit provider and model identifier; selecting a real provider without its required configuration fails clearly at Agent startup.
- [x] The intent contract covers language, dialect, intent, normalized Constraints, missing fields, and clarification state without accepting model-authored policy decisions.
- [x] Money remains an exact decimal string plus ISO currency until deterministic validation constructs `Money`.
- [x] A scripted client remains available only when explicitly selected and powers ordinary deterministic tests without network access.
- [x] `.env.example` documents placeholders, `.env` remains ignored, and no credential can reach the Panel, Bridge, Storefront, browser bundle, fixtures, or logs.
- [x] Contract tests cover valid output, malformed output, unsupported schema versions, missing configuration, and accidental silent fallback.

## Comments

- Approved provider order: NVIDIA NIM for local development, Amazon Bedrock later through a separate adapter.
- The model interprets language and proposes typed output; deterministic code retains currency, safety, confirmation, identity, sequence, and navigation enforcement.
- Implemented with an explicit scripted default for tests and local evaluation; real-provider adapters remain separate follow-on work.
