# Linux production runtime preparation plan

> **For agentic workers:** Use superpowers:executing-plans with TDD and one final fresh review. The owner explicitly requested immediate continuation of host preparation.

**Goal:** Replace the development-lock ambiguity with a separately verified,
hash-pinned Linux runtime input contract packaged in each new release.

**Architecture:** Preserve the existing application, native launchers and release
builder. Prepare the 28 already rehearsed runtime wheels as a separate lock; a
preparation-only verifier checks actual wheel identity, target compatibility and
dependency closure. Package both contract and lock with immutable release files.

**Tech stack:** Python3.12, existing packaging26.3 preparation tooling, pytest,
retained network-isolated AL2023 image and existing hash-checked wheelhouse.

**Spec:** Existing host design/constraints in
`docs/superpowers/specs/2026-10-23-cap06-linux-host-design.md`,
`docs/superpowers/specs/2026-10-23-cap06-host-isolation-design.md` and current
`PROJECT_CHECKPOINT.md`; owner continuation and scope clarification on24October.

## Global constraints

- Controlled Storefront only. Step25 is parked, unmerged and out of scope.
- No account/provider/AWS calls, paid tests, real keys/state, host installation,
  service/user/firewall changes, public TLS/DNS or activation.
- Keep root development requirements.lock and existing direct package pins.
- Include uvicorn standard extras and the existing uvloop0.22.1 Linux candidate;
  exclude diagnostic packaging and development/editable installs from runtime.
- Target CPython3.12/Linux x86_64/glibc2.34; tested patch3.12.15 is marker/rehearsal
  evidence, not a selected/approved EC2 interpreter or AMI.
- Existing derived Windows rehearsal and Git-stubbed packaging diagnostics stay
  historical; native clean-source release/provisioning acceptance remains open.
- Owner permits current OpenRouter fallback if Bedrock is unusable. Keep explicit
  selection and existing non-resetting$2 cap; no silent switch or new call authority.

## Review focus

- Linux marker/extras evaluation must not inherit Windows and omit uvloop.
- Hash-valid files with the wrong wheel identity, tags or metadata must fail.
- Missing dependencies, incompatible pins and unreachable extra wheels must fail.
- Releases must retain and verify the exact Linux contract/lock bytes.
- Preparation evidence must not be labelled interpreter/security/real-host approval.

## Task1: Linux runtime contract and offline input verification

Files: new `deploy/linux-runtime.json`, `deploy/requirements-linux.lock`,
`deploy/linux_runtime.py`, `eval/tests/test_linux_runtime.py`.

- [x] Write and observe failing tests for exact direct roots, deterministic hashed
      lock, manifest drift, wrong target/identity, missing/extra dependency and
      Linux standard-extra closure; use synthetic wheels for ordinary CI.
- [x] Implement inventory(source)->dict and verify_inputs(source,wheels)->dict
      with bounded fixed refusals, no extraction/install/network and explicit
      target marker environment. Retain exact reviewed wheel identities/digests.
- [x] Prove the actual retained wheelhouse through the verifier; record results.

## Task2: Package and protect the Linux runtime inputs

Files: `deploy/artifact.py`, `eval/tests/test_release.py`.

- [x] Observe a failing release test for the two missing runtime input files.
- [x] Validate the runtime inventory before building and package its exact bytes;
      preserve development lock and existing artifact provenance/verification.
- [x] Require immutable manifest inclusion and refusal after lock alteration.

## Task3: Offline native runtime proof, review and handoff

- [x] Install only the exact28runtime wheels with require-hashes/no-index/no-deps
      into disposable network-none Linux storage. Prove distribution identity,
      default-site isolation and six native imports. No application/provider start.
- [x] Run affected release/host checks, repository format/lint/Python/TypeScript
      tests/build and pip check; retain precise failures, repairs and limitations.
- [x] Fresh whole-slice review, one material fix pass, guide/evidence/checkpoint
      updates and local commits. No push or deployment in this slice.

Next after this slice: genuine clean native release with real Git provenance,
production interpreter/package security/provisioning, real systemd boot/reboot and
Agent readiness/capacity; explicit fallback host integration/qualification and
account/cost/bound apply acceptance. This plan does not close those gates.

## Verification outcome

Runtime proof and focused checks passed; fresh code/document review found no material issues. The combined Python run had1367passes,2warnings and one MemoryError during unchanged Moto/Botocore fixture setup; that entire40testmodule passed on recheck without edits. Preserve this error and do not call the combined run green. No application/provider/AWS activation occurred.
