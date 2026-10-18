# CAP-04 release and recovery implementation plan

> **For agentic workers:** Use superpowers:executing-plans inline and the owner's implement workflow. Approved scope is local ticket 06 in docs/cap04-ticket-breakdown.md, from docs/cap04-spec.md. The owner said go; existing release/process/browser seams are approved there.

**Goal:** Install and rehearse built releases without resetting catalogue, admission or spending state, and prove restart/rollback safety locally.

**Architecture:** Small owner-only Python deployment tools create allowlisted release directories, verify manifests/configuration/storage, back up the catalogue consistently and supervise fixed local service commands. Persistent state and restricted configuration live outside releases. Built Storefront JavaScript and Panel/Bridge assets run without TypeScript loaders or development servers. No installer copies an environment file or live database.

**Stack:** Existing Python 3.12, Node 24, pnpm, TypeScript and SQLite; no new runtime dependencies. Build uses the existing pnpm offline store. Linux service hardening is supplied separately from workstation evidence.

## Constraints and review focus

- No AWS, DNS, trust changes, paid models, real invites or prompt/interpretation changes.
- Reuse the managed clean worktree; branch codex/cap04-release starts at b9248bb. Original checkout remains untouched.
- Release/rollback changes executable code only. Neither allowance nor invitation history is restored from a release or catalogue backup.
- Source and destination paths must resolve safely; existing releases/restore targets refuse replacement. Manifest tampering and incompatible/missing storage prevent service startup.
- Preserve ownership, Confirmation, Undo, stale results and uncertain Action protections across actual process restart.
- Logs have a fixed vocabulary, finite size/count and seven-day retention. Raw child output, URLs, bodies, code values and stack traces are suppressed.
- Local loopback built-browser proof and production-mode subprocess proof are separate. Historical HTTPS proof is not silently rerun or called deployed evidence.

## Task 1: Built release and compatible storage

- [x] RED CLI/artifact tests for isolated built release, no secret/state inclusion, no overwrite and compatible manifest.
- [x] Emit Storefront and shared Bridge modules; use pinned offline pnpm production dependencies. Allowlist Agent Python, definition, built assets and runtime tools; hash artifacts.
- [x] RED then GREEN preflight and catalogue backup/restore tests through public commands, including incompatible/corrupt/missing storage, occupied outputs and insufficient disk headroom.
- [x] Keep all mutable databases/configuration/logs outside releases; backup uses SQLite's online backup API with revision/content verification and exclusive output.

## Task 2: Supervision, permissions and bounded logs

- [x] RED then GREEN supervisor tests: fixed loopback services, no watcher/access log, failed health/startup, stop/restart/rollback and finite redacted diagnostics.
- [x] Explicit restricted external configuration, one worker, owner runbook and Linux service hardening. Distinguish actual workstation permissions from Linux deployment checks still required.
- [x] Startup checks storage and release compatibility before children; unexpected child exit stops siblings. Readiness requires service health; commands do not perform inference.

## Task 3: Combined restart and closure

- [x] Actual built browser journey with disposable catalogue/admission/allowance: Agent restart preserves cart, invalidates old task/result/Confirmation; Storefront restart clears cart, relinks and rejects old Undo/Confirmation. No uncertain Action replay.
- [x] Rollback between two immutable releases retains ledger/invitation identities and charged reservations; catalogue restore goes only to a new disposable copy.
- [x] Focused checks while iterating, then serial full Python/browser tests and TS tests/build/types/format/lint; independent Standards/Spec reviews and regression fixes.
- [x] Update owner runbook, checkpoint/handoff and local ticket with exact evidence and limitations; commit locally. No push/deployment implicit.

## Rulings and evidence

Ruling: reuse approved design and proceed without reopening policy questions — the owner explicitly selected ticket 06 and implementation. No new deployment/spending permission is inferred.

Ruling: release dependency installation is offline and pinned by the existing lockfile. This proves workstation installation; the eventual Linux build must use its own pinned runtimes and repeat verification, not copy Windows dependencies.

## Execution ledger

- Built release, exclusive install, online WAL backup/restore, compatibility,
  fixed-vocabulary diagnostic limits, production route isolation, rollback and
  the built-browser restart journey: nine focused tests pass in 149.60s.
- TypeScript: 199 tests, builds, recursive type checks and ESLint pass.
- Native Linux/WSL DAC proof passes as UID 65534 with immutable code/configuration,
  writable state and other-account configuration denial. No host accounts or
  services were installed. Caddy adapts the bounded external diagnostic config;
  no TLS/CA changes were made.
- Ruling: pnpm's legacy deploy writes workspace dependency-state metadata, so it
  now runs in a disposable manifest-only workspace. A regression verifies the
  actual checkout dependency-state file is unchanged. Internal workspace self-links
  are removed; external/dangling links fail verification.
- Ruling: Windows owner shutdown must terminate the exact owned process tree and
  wait for socket closure before restart. Native Windows abrupt external termination
  of a venv launcher is not qualified; the deployed Linux unit uses control-group
  shutdown. Normal owned restart is covered by actual cart/authority tests.
- Independent Spec review: no material gaps. Standards review identified ignored
  executable Python caches as a verification bypass. A real compiled cache
  reproduced the bypass; rejection now passes, and both review axes cleared it.
- Final serial full regression: 696 Python/browser tests pass in 691.70s. All
  relevant checks pass; local ticket 06 is resolved, parent CAP-04 remains open.
- Ruling: the first full-suite tool session was unavailable after chat resumption.
  It is not completion evidence; the final rerun writes an ignored local log and
  exit-code record so its result survives another interruption.

## Standards

One material finding was reproduced and fixed: ignored executable caches could
bypass artifact verification. The real-bytecode regression passes and the reviewer
cleared the fix. No unresolved material Standards findings. Windows abrupt external
launcher termination remains disclosed, with Linux control-group checks deferred
to deployment acceptance.

## Spec

No material gaps or scope findings. Both initial implementation and final bytecode
follow-up were independently reviewed. Local proof remains distinct from deployed
Linux/EC2 qualification; rollback selection does not claim compatibility with an
untested older product/schema version.

Final status: zero unresolved findings on either axis. Code is committed locally;
no push, domain changes, provisioning, participant contact or paid calls.
