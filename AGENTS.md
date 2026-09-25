# Agent Instructions

## Start here

- Read `CONTEXT.md` before naming or changing domain concepts.
- Read `PROJECT_CHECKPOINT.md` before implementation work to recover the current frontier and verified evidence.
- Read `handoff.md` when joining the project or resuming after a context reset; use `PROJECT_CHECKPOINT.md` for the newest status when historical sections differ.
- Use `MVP_PLAN.md` as the local MVP scope and `IMPLEMENTATION_PLAN_FINAL (1).md` as the ordered execution plan.
- Read `.scratch/shopping-copilot-local-mvp/spec.md` before product work. Its approved behaviour decisions override older plan wording when they conflict.
- Work on the next incomplete plan step unless the user explicitly reprioritizes the work.
- Keep each change within the active step and preserve unrelated user changes.

## Product gates

- Complete the local MVP gate before independent-storefront generalisation.
- Complete the generalisation gate before AWS or production-readiness work.
- Preserve the safety invariants: off-origin navigation is blocked, Sensitive Field values are excluded, Guarded Mutations require bound Confirmation, and stale or duplicate Actions are rejected.
- Preserve refresh recovery without automatically replaying an Action whose outcome is uncertain.

## Verification

- Test externally observable behaviour at the highest practical seam.
- Run focused checks while iterating, then the repository's relevant format, lint, test, and build commands before declaring work complete.
- Treat every safety invariant affected by a change as a required regression test.

## Agent skills

### Issue tracker

Specs and tickets are local Markdown files under `.scratch/`. See `docs/agents/issue-tracker.md`.

### Triage labels

Use the default five-role triage vocabulary. See `docs/agents/triage-labels.md`.

### Domain docs

This is a single-context repository despite its package layout. See `docs/agents/domain.md`.
