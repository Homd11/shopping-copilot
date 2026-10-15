# Durable inference allowance implementation plan

> For agentic workers: use superpowers:executing-plans inline, one public-seam TDD slice at a time.

**Goal:** Complete CAP-04 local ticket 05 without paid calls or AWS resources.

**Architecture:** An explicitly initialized SQLite ledger outside disposable releases
atomically reserves exact USD amounts. A provider-neutral LLMClient decorator bounds
concurrency and waiting, reserves before calling its delegate, settles verifiable
cost once, and retains unknown charges. Production real providers require this
configuration; local development remains unchanged unless opted in.

**Tech stack:** Python standard-library SQLite/Decimal/asyncio, existing LLMClient
and FastAPI seams. No extra package or prompt/schema changes.

**Spec:** `docs/cap04-spec.md`, ticket 05 in `docs/cap04-ticket-breakdown.md`.
The owner selected ticket 05 and inline execution under this already-approved scope.

## Constraints and interfaces

- Public seams: ledger operations plus complete(), process restart and HTTP pause
  outcomes, as specified by the approved verification strategy.
- Use integer nanodollars with conservative upward conversion, explicit rates
  per million input/output tokens, and a conservative serialized-byte input bound.
- Each guarded delegate receives one provider attempt. Interpretation, advice and
  their repair calls all share the same configured decorator.
- SQLite `mode=rw` never creates missing runtime storage. Schema/ledger identity
  mismatch, corruption, full or unwritable storage refuse inference.
- Exclusive initialization is an owner CLI operation. Persistent kill switch can
  be toggled by that CLI; toggling never changes allowance or reservations.
- Ledger contains IDs, amounts and accounting state, no prompts, identities or keys.
- Keep provider-specific receipt extraction in adapter wiring. Missing, invalid,
  failed or cancelled-call cost stays reserved; settlement exceeding a reservation
  disables further inference. Do not claim verified Bedrock prices or entitlement.
- Production configuration must supply ledger path/identity, finite concurrency,
  queue/wait bounds and explicit prices. Five-Shopper EC2 capacity is still unproven.
- Release rollback keeps the same ledger; never restore an old ledger balance.

## Review focus

1. Two Agent objects/processes reserving the final allowance concurrently.
2. Cancellation or abrupt termination after provider entry, before settlement.
3. Missing or substituted initialized storage after successful startup.
4. A queued request seeing a persisted kill switch before its provider call.
5. Settlement/storage failure after a completion, before execution sees its text.

## Slices

- [x] Ledger: explicit initialization, atomic reserve/settle, status, kill switch;
      restart, duplicate IDs/settlement and concurrent final-allowance regression.
- [x] Decorator: explicit fake prices/provider, bounded wait/concurrency, conservative
      unknown-cost retention, cancellation and no output on failed settlement.
- [x] Runtime/config/CLI: one shared boundary for every LLM request, production
      requirement, clear budget/busy/disabled/storage pause reasons, owner instructions.
- [x] Process/storage acceptance: killed invocation and reopen, missing/corrupt/
      read-only/full storage refusal at public seams.
- [x] Focused tests during slices, relevant full offline checks once, independent
      Standards/Spec reviews, evidence/checkpoint, ticket closure and local commit.

No inference allowance is initialized on the owner's real key or deployment by
these tests. The separately approved model replacement is qualified; see docs/research/2026-10-15-gemini-replacement.md. Ticket05 acceptance: 665 Python/198 TypeScript, format/lint/build and independent runtime reviews pass.
