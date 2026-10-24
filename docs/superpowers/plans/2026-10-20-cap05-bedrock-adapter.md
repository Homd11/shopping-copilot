# CAP-05 Bedrock adapter implementation plan

> **For agentic workers:** Use superpowers:executing-plans inline, with TDD and a
> final independent review. Existing isolated worktree, no AWS execution.

**Goal:** Make the first Bedrock candidate usable through the existing provider
boundary with deterministic offline safety/failure evidence.

**Architecture:** Non-streaming Converse via lazy boto3, asynchronous worker with
cancel drain, local output validation, bounded metadata and existing durable guard.

**Tech stack:** Python 3.12, boto3/botocore, pytest; unchanged TypeScript services.

**Spec:** `docs/superpowers/specs/2026-10-20-cap05-bedrock-adapter-design.md`.
Base: `7b9fc8a`.

## Global constraints

- No AWS calls, resources, credentials, active-provider switch or paid qualification.
- No interpreter, browser Action or safety-policy changes; one provider attempt.
- Only explicit eu-north-1 / openai.gpt-oss-20b-1:0 candidate for this slice.
- Keep uncertain reservations; no inferred USD receipt; never reset allowance.
- Keep local02/final09/parentCAP-04 and liveCAP-05 unaccepted.

## Review focus

- Canceled SDK workers cannot silently outlive released inference slots.
- Malformed success/error bodies cannot escape as text or leak into metadata.
- Factory/configuration must not fetch credentials or invoke a provider.
- Schema instructions fit existing reservation; tools and unbounded requests refuse.
- Native retries and configured prices cannot bypass one-attempt cost control.

## Task 1 — Adapter and configuration

Files: create agent/llm/bedrock.py and agent/tests/test_bedrock.py; modify
agent/llm/config.py, factory.py, **init**.py, agent/app.py, pyproject.toml and
requirements.lock. Interface: BedrockClient.complete(LLMRequest) yields LLMChunk;
BedrockProviderError carries a safe pause category.

- [x] Add failing tests for factory/configuration, Converse payload and local
      validation; run focused pytest and observe missing adapter failure.
- [x] Add pinned SDK dependencies and minimal adapter/configuration wiring.
- [x] Add focused rejection/error/metadata/cancel/late-authority/SDK contract tests,
      observe failures, then implement the bounded behaviors.
- [x] Run focused provider/configuration regressions and Ruff.

## Task 2 — Spending integration and qualification handoff

Files: agent/inference/config.py, agent/tests/test_bedrock.py, docs/cap05-bedrock.md,
PROJECT_CHECKPOINT.md and handoff.md; local tracker copied/updated without closure.
Interface: configured_guard validates candidate price floor; no Bedrock receipt
callback is registered, so current ensure_accounted preserves unknown costs.

- [x] Add failing integration tests proving retained reservation and rejecting
      prices below the candidate floor; implement floor check.
- [x] Document local evidence, optional credentials/SDK setup for future use,
      exact limits and remaining live qualification/cost-receipt work.
- [x] Run full Python/browser suite, TS tests/build/types/lint/format once; record
      output and distinguish any tooling/environment failures.
- [x] Independent review, fix material findings, verify and commit explicit files
      locally. No push or merge.

## Execution ledger

Pre-flight: Task2 consumes Task1 metadata/configuration and complete boundary;
the guard already retains reservations when receipt is absent. No settlement
interface changes or ledger schema migration are needed.

Ruling: the owner selected the already described offline adapter slice; SDK and
schema-format choices are implementation details, not a new product feature.
Proceed with this scope without repeating architecture or spending approval.

Task1: RED16 failures observed (missing adapter/SDK and configuration checks), then
GREEN16. Additional failure integration/pricefloor tests observed6 failures,
fixed SDK closing (botocore clients do not implement context-manager entry), safe
pause mapping, timeout classification and pricefloor. Dependency pins installed;
pip check passes. SDK operations remain stubbed with dummy credentials.

Final review: independent reviewer found two important edge cases: lossy schema
reference-sibling sizing and valid rolling history starting with assistant text.
Both have observed RED/GREEN regressions. The shared guard now uses the canonical
inline schema expansion, and a fixed synthetic user marker preserves original
leading assistant context. Reviewer recheck clear;79 focused provider/guard/schema/
contract tests pass. No changes to interpreter, catalogue grounding or Action
permissions. Full code regression is running; live qualification remains pending.

Ruling: fixing the reservation representation is required by this adapter's
spending boundary. Reuse existing provider_schema helper rather than duplicating
it; old non-definition/cyclic references still fail closed. Price/receipt policy
and ledger schema remain unchanged.

Verification in progress: TS199tests, recursivebuild, explicitPaneltypecheck and
ESLint pass. Prettier/Ruffcheck/format pass. FullPython/browser755case run has
reported one bilingual browser-journey failure; preserve the full result and
reproduce that node serially after completion. Do not label the suite green or
change product behavior without its failure trace and a reproduced cause.

Final verification: full Python/browser755cases returned754passed/1failed in
761.94s (exit1), two upstream WebSocket warnings. The bilingual-discovery test's
Franco-Arabic case exceeded its10-second deadline. Three serial reruns of that
unchanged test passed (21.74/21.85/22.11s); failure remains documented, root cause
unknown. No deadline change, no product fix claimed and no original full-green
claim. Separate TS199, builds, Panel types, lint, format and pip check pass.

Final review recheck: both Spec/safety findings resolved;39 Bedrock tests pass.
Standards review clear. No deferred code findings. Remaining limitation: the
single unestablished browser timing failure and all live model/account evidence.
Source/credential scans and explicit local commit finish this offline slice;
CAP05's live acceptance criteria remain unchecked.
