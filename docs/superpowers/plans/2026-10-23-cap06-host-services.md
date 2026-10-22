# Host service bundle implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Prepare Storefront/Caddy launch and target wiring around the existing Agent.

**Architecture:** One protected Python entry validates the selected component and
execs a fixed binary with an allowlisted environment. Systemd owns the three
processes via separate inactive units and an explicitly controlled target.

**Tech Stack:** Python3.12, Node24, pinned Caddy2.11.7, systemd units, pytest.

**Spec:** `docs/superpowers/specs/2026-10-23-cap06-host-services-design.md`.

## Global constraints

- No AWS/model calls, public ACME run/validate, deployment, unit installation or spend.
- Existing protected settings, exact release and closed qualification gate persist.
- Fixed `/usr/bin/node`, `/usr/bin/caddy`, loopback Storefront and public profile.
- Existing external catalogue and `/var/lib/shopping-copilot/caddy`; never initialize state.

## Review focus

- Ambient execution/proxy/evaluation/credential variables must not reach children.
- A valid manifest from another executing release must not authorize exec.
- Unsafe retained certificate storage must refuse before running Caddy.
- Target ordering must avoid cycles and overlapping legacy port ownership.
- Native launch order must not be reported as HTTP, TLS or provider readiness.

## Task 1: Protected component exec and packaged service bundle

**Files:** create `deploy/host_component.py`, Storefront/proxy service files and
`deploy/shopping-copilot-host.target`; modify Agent unit and artifact allowlist;
create `eval/tests/test_host_component.py`, extend `eval/tests/test_release.py`;
write `docs/cap06-host-services.md`, evidence and checkpoint.

**Interfaces:** consume `HostSettings`, `load_host_settings`, `catalogue_status`;
produce `command(settings, component) -> (argv, environment)` and `main(argv=None)`.
Internal `_storage(path)` validates protected existing POSIX directory;
`_version(binary, environment)` performs bounded fixed version validation.

- [x] Write tests for clean fixed store/proxy commands, no parent mutation or SDK,
      release mismatch, missing/tampered packaged inputs, catalogue/storage failure,
      version floor/pin/timeout, exact exec and generic CLI failure. Assert no child
      inherits credentials, Node injection, key or unrelated inference configuration.
- [x] Run new component tests and observe missing implementation/unit failures.
- [x] Implement minimal fixed exec preparation and redacted CLI, no public bypass.
      Add hardened units/target with documented Wants/PartOf/After/Conflicts semantics,
      protected retained proxy storage and Caddy-only bind capability. Include all in
      the artifact allowlist and fresh release tests.
- [x] Exercise real packaged production Storefront via the generated environment,
      using existing catalogue and fixture secret; prove test/private-route access
      boundaries and state history without starting Agent or Caddy. Run existing
      real-Caddy adaptation tests, no public-profile provisioning.
- [x] Run focused component/host/package/proxy tests, then all-Agent/host/control/
      release/browser regressions. Run Ruff check/format, pip, TS lint, changed
      Markdown/JSON Prettier and whitespace. Expected: pass, no model/cloud calls.
- [x] Record available static systemd parsing with precise limits, primary research,
      evidence and checkpoint. Fresh final reviewer checks the five review-focus
      conditions and whole slice. Fix actionable issues with regression evidence.
- [x] Commit verified explicit files locally; retain ongoing branch, no push/apply.
