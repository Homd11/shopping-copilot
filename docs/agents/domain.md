# Domain Docs

This repository uses a single domain context even though its implementation is split across several packages.

## Before exploring

- Read `CONTEXT.md` at the repository root before work that names, changes, tests, or documents domain concepts.
- Read relevant records under `docs/adr/` before work affected by a recorded architectural decision.
- If either location does not exist, proceed without creating placeholders.

## Vocabulary

Use the canonical terms from `CONTEXT.md` in specs, tickets, tests, interfaces, and user-facing copy. When a needed concept is absent or conflicts with existing language, resolve the term with the user and update the glossary before continuing.

## Decisions

Create an ADR only for a decision that is hard to reverse, surprising without context, and the result of a genuine trade-off.
