# Linux host rehearsal implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan inline. Steps use checkbox syntax for tracking.

**Goal:** Replace primitive-only Linux evidence with full protected host modules
and native executable rehearsal, plus a documented cost/inventory reconciliation.

**Architecture:** Prepare explicit vendor/hash-locked inputs locally, derive a
portable verified release, and run a standard-library bootstrap/probe in the
retained network-isolated AL2023 container. No production runtime code changes.

**Tech stack:** Python3.12, Docker, native Node24.13.0/Caddy2.11.7, existing release
builder, pinned Linux wheels and pytest.

**Spec:** `docs/superpowers/specs/2026-10-23-cap06-linux-host-design.md`.

## Global constraints

- No AWS/account/model calls or public Caddy run/validate; no host/system installation.
- Test-only explicit dependency profile, unchanged production locks and closed provider.
- Derived rehearsal artifact retains upstream provenance; not byte-identical artifact acceptance.
- No real keys/state, mounted credentials, external runtime network or Docker socket.

## Review focus

- Cross-platform dependency markers must include Linux Uvicorn standard dependencies.
- Release-link transformation must refuse external targets/cycles and bound input.
- Full default protected reader must run without a trusted-reader replacement.
- Native Storefront exec may use loopback only; public Caddy run must never execute.
- Cost scenarios must distinguish two functions, shared allocations and unverified account facts.

## Task 1: Reproducible isolated probe and evidence

**Files:** add `eval/linux_host_fixture.py`, `eval/linux_host_probe.py`,
`eval/tests/test_linux_host_fixture.py`, a diagnostic runtime input manifest under
`eval/`, evidence/guide; update checkpoint/handoff. Keep acquisition/staging ignored.

- [x] Test portable release extraction/links/bounds and refusal; observe RED.
- [x] Implement minimal verified portable fixture preparation and complete Linux
      probe, using the existing builder's artifact verification and no production edits.
- [x] Acquire/stage public vendor archives and target wheels; retain digests and
      explicit dependency closure. Build production release, prepare and hash inputs.
- [x] Run exact offline AL2023 non-root bounded container; require full reader,
      native exec/adapt, state preservation, negative config and no-SDK/network results.
- [x] Recompute the cited cost scenarios with Decimal, distinguish selected versus
      conditional resources, double-counting/timeout sensitivity and remaining blockers.
      Record current public-rate evidence, never current account eligibility or spend approval.
- [x] Run focused fixture/host/config/release checks appropriate to new verification
      tools; Ruff, pip, changed Markdown/JSON formatting and whitespace. Existing
      runtime is unchanged; no blanket repeat of unrelated Agent/model/browser suites.
- [x] Fresh final review, fix actionable failures, record limitations/checkpoint and
      commit explicit files locally. No push, resources, units or public HTTPS activation.
