# CAP-06 inactive lifecycle observation implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL superpowers:executing-plans inline,
> test-driven-development and fresh independent final review.

**Goal:** Prepare a browser-independent tick and disabled reviewable scheduling bundle.
**Architecture:** Reuse current authority/controller/ZIP roles; pure conditional
Scheduler/IAM/alarm documents, no SDK administration or active resource selection.
**Tech Stack:** Python3.12, existing boto3/HTTPX, JSON EMF, Moto/Stubber offline tests.
**Spec:** docs/superpowers/specs/2026-10-22-cap06-observation-delivery-design.md.

## Global constraints

- No real AWS/model/credential/resource/key/DNS/TLS call/write, activation or spend.
- Selected cloud inventory remains unchanged until final explicit resource review.
- No wake creation, activity extension, expired lease recovery or uncertain replay.
- Keep strict dispatch/observe behavior and two fixed-role artifacts.
- Windows, Moto and disabled documents do not establish Linux/deployed acceptance.

## Review focus

- Lost dispatch notification must not strand a still-valid unclaimed wake forever.
- Revoked/expired/deadline/stale/uncertain commands cannot be retried by ticks.
- Tick failure must reach Errors despite existing generic entry wrappers.
- Browser traffic must not emit the schedule completion metric or mask missing ticks.
- Scheduler trust uses group ARN and render always disables schedule/alarm actions.

## Task 1: bounded trusted tick and telemetry

**Files:** agent/lifecycle/controller.py, lambda_runtime.py, lambda_entry.py;
agent/tests/test_control_tick.py, test_lambda_entry.py.
**Interfaces:** ControlWorker.handle({kind:tick}); existing runtime same signature.

- [x] RED stopped no EC2/write; lost-notification valid start; duplicate/unknown/
      revoked/expired/deadline cases; closed-browser idle/leases/activity races.
- [x] Implement fresh observation then one existing pending command, no loops.
- [x] RED bounded tick-only EMF success and generic failure propagation through
      actual entry/config/factory path; implement and GREEN existing regressions.
- [x] Instrument intercepted SDK calls and DynamoDB item bytes for representative
      stopped/starting/ready/128lease/drain/stop cases; report assumptions honestly.

## Task 2: disabled pure resource proposal

**Files:** deploy/observation.py, eval/tests/test_observation.py.
**Interface:** frozen ObservationBindings + render_observation(bindings) -> dict.

- [x] RED exact fixed target/group trust/role, UTC finite60day maximum, retry/age,
      disabled schedule, memory/timeout/concurrency, EMF/error alarm scope/no actions.
- [x] Implement validation/render only; no SDK/env/clock discovery or apply command.

## Task 3: verification and record

- [x] Rebuild both actual role ZIPs twice; external hashes and isolated smoke.
- [x] Full affected tests/fresh release build/lint/format; fresh review fixes.
- [x] Evidence/checkpoint/handoff and local commit; no resource adoption or apply.

## Execution ledger

Preflight: Task1 reuses existing executor transaction filters. Task2 emits disabled
input for future deployment only and cannot start resources. Existing allowlist
already includes changed controller/runtime/entry sources. No conflicting APIs.
Ruling: owner's go authorizes reversible local preparation after costed proposal
and clear builder check; no further permission loop for offline code. Proposed
new service and USD23 allocation are not adopted or spent until separate concrete
resource/cost/rollback approval. Existing $0 cash and all open gates persist.

Builder check clear. Tick tests11FAIL/1PASS plus pending-stub teardown errors RED
(existing event rejection); implementation GREEN84tick/entry/runtime/worker cases
20.85s. Renderer missing-module RED then14GREEN0.07s. Added actual concurrent CAS,
probe/activity, live/expired lease, late cleanup and6operation profiles; combined
36GREEN11.40s. Most active profile26hotGet/3transactions;128lease item6868JSONbytes;
cold constructor adds4Get, no actual billing inference. Independent final reviewer
clear;108focused and existing cases33.72s. Both updated ZIPs rebuilt identically,
externally verified and isolated Windows3.12smoke passed with SDK/network forbidden.
Final affected suite1036passed/no skips170.67s including fresh release build.
Ruff247files/pip/ESLint/Prettier/whitespace pass. No source edits after review.
Artifact Linux execution and actual resource eligibility/adoption/apply remain open.
