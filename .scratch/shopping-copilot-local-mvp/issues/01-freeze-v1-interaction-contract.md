# 01 — Freeze the v1 interaction contract

**What to build:** Establish the small, versioned protocol that lets the Agent and Bridge exchange Snapshots, Actions, and Action Results without interpreting the same message differently.

**Blocked by:** None — can start immediately.

**Status:** resolved

- [x] Snapshot, Action, and Action Result each carry an explicit v1 version and have representative shared fixtures.
- [x] The question Action uses the canonical v1 name `ask_shopper`; older `ask_user` wording is not part of the contract.
- [x] The Python and TypeScript representations accept and round-trip the same valid fixtures.
- [x] Both representations reject incompatible versions and malformed required fields.
- [x] Sensitive elements can be represented as metadata marked sensitive without carrying a value.
- [x] Contract tests run through the repository's normal test commands.
