# Fixed vendor runtime alignment plan

> **For agentic workers:** Use superpowers:executing-plans with TDD and one fresh final review. Continue authorized host preparation; no resource or model activation.

**Goal:** Align preparation inputs with the actual selected AL2023 repository's
Python3.12.14 and the current signed Node24.22.1 security candidate.

**Architecture:** Preserve historical Lambda/Python3.12.15 evidence. Verify vendor
RPM signatures and bounded private extraction, then execute the candidate in the
retained isolated AL2023 image. Keep the same28application wheels and development
lock. A new clean native build must bind the updated preparation target and tools.

**Spec:** Current host/bootstrap/isolation contracts, newest checkpoint, and
docs/research/2026-10-24-cap06-production-host-adoption.md. These are implementation
choices for approved native host preparation, not new product scope.

## Constraints and review focus

- Controlled Storefront only. No independent-storefront generalisation.
- No actual host/package installation, AWS resource creation/update, public
  activation, real key/ledger change, model call/spend, upgrade, push or merge.
- Prior account preflight uses read-only metadata after owner reauthentication;
  current Free-plan/credit/quota observations are not permission to apply.
- Vendor RPMs/public key and Node signed checksums must verify before execution.
- Private prefix and fixed library path only in disposable process environment;
  no owner system Python, PATH, GPG/RPM database or image mutation.
- Actual Python patch, ABI, native imports and closure must match the new target.
  No Lambda-site fallback, provenance stub, manifest rewriting or blanket claim
  that ABI compatibility establishes real host/security acceptance.
- production_interpreter_approved remains false until actual host adoption.

## Task1: Candidate acquisition and source reconciliation

- [x] Observe vendor Python3.12.14 core startup from signature-verified RPMs; retain
      missing-library failures and acquire their signed fixed-release providers.
- [x] RED wheel Requires-Python patch-boundary regressions; update only Linux
      preparation target/fixtures from3.12.15 to3.12.14. Keep root requirements.lock
      and the28wheel versions/hashes unchanged; GREEN complete runtime tests.
- [x] Bind the native build tool to Node24.22.1 and the private interpreter prefix.
      Reject missing/wrong private runtime inputs; environment paths remain fixed.

## Task2: Actual vendor runtime and release proof

- [x] Require real3.12.14 prefix/ABI/stdlib native imports and pip from verified
      candidate files, with no image-site fallback. Diagnostic tools stay external
      to the28application distributions.
- [x] Commit source, capture original clean commit/tree, run frozen offline pnpm
      and hash-locked wheel install plus the unchanged release builder under the
      vendor interpreter and signed Node24.22.1. Preserve actual manifest/source.
- [x] Repeat native Storefront/Agent startup, signed default-closed readiness,
      permission/allowance/uncertainty/persistence and bounded shutdown/refusal.
- [x] Focused runtime/release/host tests, relevant source checks and fresh review.
      Record exact interpreter/libs/tool/runtime/archive digests and proof limits;
      update checkpoint/inert proposal and commit locally.

Actual EC2/AMI installed package state, systemd/users/reboot/security acceptance,
real authority/provider qualification/custody/capacity and exact cost/resource/
rollback/public activation gates remain open.

## Verified outcome —24October

Clean native source2c9ae36 built under actual signed vendor Python3.12.14 and
Node24.22.1. Storefront checks, actual synthetic-authority Agent startup with
closed provider readiness, shutdown/refusal and independent archive extraction
all pass.62runtime/bootstrap/probe tests and140release/source/host checks pass;
source lint/format/pipcheck pass. Exact immutable profiles/results and remaining
adoption gates: docs/cap06-vendor-runtime-alignment.md and its evidence record.
No root dependency/wheel version change, model spending, actual key/ledger
change, resource creation/public activation, push or merge.
