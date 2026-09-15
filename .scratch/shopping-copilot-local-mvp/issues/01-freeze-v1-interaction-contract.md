# 01 — Freeze the v1 interaction contract

**What to build:** Establish the small, versioned protocol that lets the Agent and Bridge exchange Snapshots, Actions, and Action Results without interpreting the same message differently.

**Blocked by:** None — can start immediately.

**Status:** ready-for-agent

- [ ] Snapshot, Action, and Action Result each carry an explicit v1 version and have representative shared fixtures.
- [ ] The Python and TypeScript representations accept and round-trip the same valid fixtures.
- [ ] Both representations reject incompatible versions and malformed required fields.
- [ ] Sensitive elements can be represented as metadata marked sensitive without carrying a value.
- [ ] Contract tests run through the repository's normal test commands.
