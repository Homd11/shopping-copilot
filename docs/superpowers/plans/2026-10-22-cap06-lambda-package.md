# CAP-06 Lambda package implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL superpowers:executing-plans inline,
> test-driven-development and one fresh independent final review.

**Goal:** Build verifiable offline startup/controller ZIPs for Python 3.12.
**Architecture:** Fixed-role lazy entry over existing runtime factories; strict
universal-wheel assembly with exact hash lock and self-contained artifacts.
**Tech Stack:** Python 3.12 stdlib, build-only packaging 26.3, existing boto3/HTTPX.
**Spec:** docs/superpowers/specs/2026-10-22-cap06-lambda-package.md.

## Global constraints

- No AWS/model/credential/resource/DNS/TLS calls or writes, activation or push.
- No scheduler/topology/gate/spend change; keep fixed Stockholm runtime factories.
- Exactly 14 pure wheels; no native/dev packages, keys, config, state or bytecode.
- Windows verification is not Linux execution or deployed acceptance.

## Review focus

- Malformed/cross-role config must fail before SDK creation without disclosure.
- Failed initialization must not repeat an uncertain operation on warm invocation.
- Wheel metadata, RECORD and path attacks must fail before artifact publication.
- Manifest edits alone cannot authorize changed executable package bytes.
- Artifact imports must work without installed dependencies or checkout fallback.

## Task 1: fixed-role lazy entry

**Files:** agent/lifecycle/lambda_entry.py, agent/tests/test_lambda_entry.py.
**Interface:** make_entry(role, \*, environment=None, factory=None) -> handler.

- [x] RED tests for import side effects, exact role/schema/key validation,
      environment snapshot, generic failures, cached success and latched failure.
- [x] Implement bounded parser and role-pinned cached entry; GREEN.

## Task 2: offline wheel and ZIP assembly

**Files:** deploy/lambda*package.py, deploy/lambda-wheels.json,
deploy/lambda-requirements.lock, eval/tests/test_lambda_package.py.
**Interfaces:** build(source, wheels, output, *, role) -> manifest;
verify(path, \_, expected_sha256) -> manifest. CLI build/verify for local use.

- [x] Generate exact locks from acquired public publisher wheel bytes.
- [x] RED malicious wheel/lock/path/closure tests, deterministic ZIP and external
      digest tests; implement restricted validation and exclusive output; GREEN.
- [x] Build both roles from actual wheelhouse; isolated -I -S -B import/delegation
      and byte-identical rebuild checks, no SDK/network calls.

## Task 3: evidence and final review

- [x] Fresh affected Agent/package/host/access/build checks, Ruff and TS formatting.
- [x] Fresh independent final review; reproduce/fix actionable findings.
- [x] Record artifact hashes/limits and guide, update checkpoint/handoff, commit
      locally. Keep all unresolved cloud/model/Linux acceptance gates explicit.

## Execution ledger

User's repeated go continues inline reversible preparation in the existing
approved topology. Preflight: Task 2's generated entry imports Task 1 make_entry;
role is build-time literal, config is separate runtime input. The whole-dependency
lock is independent of the Windows development environment. No conflicting API.
Ruling: use ZIP_STORED and a 50 MiB ceiling for deterministic bytes without
compression-toolchain drift; the complete narrow package must fit before publish.

Builder check: nothing important left. Entry missing-module RED,32GREEN0.56s.
Package missing-module RED; initial valid synthetic wheel fixtures exposed missing
py2 tags on two dual-tag wheels, corrected fixture metadata;25GREEN2.14s.
Real build correctly refused JMESPath's `.data/scripts/jp.py`. Ruling: verify this
exact unused CLI's RECORD/hash then explicitly omit and record it, rather than
implement an unnecessary script installer or discard required runtime files.
RED exact-CLI case then58combinedGREEN3.81s. First real startup isolated smoke
passed: no site/checkout fallback, SDK/network forbidden, actual models/CA present.

Two provenance mutation tests reproduced missing validation (RED), then reused
the exact lock validator for verification;64focusedGREEN3.76s. Offline pip target/
hash acquisition from retained wheelhouse passed. Both role packages rebuilt
byte-identically, external digests verified and isolated smoke passed. Independent
reviewer reproduced both actual builds/smokes and64tests5.05s; no findings.
Final full affected suite1000passed/no skips161.48s, including fresh release build.
Ruff check/format244files, pip, ESLint, Prettier and whitespace pass. No source
changes after review; documentation/evidence only. Linux/deployed/model gates open.
