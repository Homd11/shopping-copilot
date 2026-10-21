# Remote lifecycle arbitration implementation plan

> **For agentic workers:** Use superpowers:executing-plans inline with test-driven
> development and a fresh final review. No external control or factory activation.

**Goal:** Persist safe wake, work/drain arbitration and single-use command handoff
using the existing injected DynamoDB authority, with no real EC2 dispatch.

**Architecture:** One bounded lifecycle item serializes admission/work/state through
identity/schema/revision conditions, with invitation validity in wake/start-claim
transactions. Command claims never expire into another dispatcher; uncertainty
blocks new generations. Existing local implementation and active runtime stay intact.

**Tech stack:** Python3.12, existing Boto3, optional pinned Moto5.2.4, pytest.
**Spec:** docs/superpowers/specs/2026-10-21-cap06-remote-lifecycle.md.
**Base:**15406ba; existing isolated codex/cap04-capacity worktree, native inline work.

## Global constraints

- Preserve3600idle/300start/120grace/5drain/45lease/60cooldown/120stop seconds,
  at most128live leases and one command. Reads/background traffic never touch activity.
- Only explicitly initialized schema1/identity authority may mutate. No reset/TTL.
- Client Stockholm/standard HTTPS/5connect15read/total_max_attempts1 rechecked perop.
- No AWS account/network requests, real EC2 commands, HTTP exposure, model calls,
  active factory/provider changes, resource/DNS/certificate/upgrade actions or push.
- Claims/uncertain outcomes never expire or silently replay; no Action replay.

## Review focus

1. Admission vs stop commitment requires one CAS boundary, not pre-read busy count.
2. Startup invitation must remain valid in the actual wake/claim transaction.
3. A paused dispatcher can outlive any timeout: no generation advance while its
   command claim/uncertainty exists, even if the host is observed stopped.
4. Stale readiness observations need both revision and generation binding.
5. Malformed/oversized state, invalid numbers, backward clocks and unknown writes
   must refuse without creating new state or clearing accepted work.

## Files and interfaces

- Create agent/lifecycle/dynamodb.py: `DynamoLifecycle(invitations, identity,
*, clock=time)` validates existing state; explicit class initialize(invitations)
  exclusively creates lifecycle#host under metadata. No SDK creation.
- Public work-compatible methods: status, wake, manual_start, begin_work,
  renew_work, end_work. Generation is required on begin/end (renew token is bound
  by the generation's map). Caller must not pass browser-selected authority.
- Trusted controller methods: observation*token() returns generation/revision;
  reconcile(token, *, instance*state, healthy) mutates only matching state;
  claim_command() returns None or private receipt with id/claim/operation/generation;
  complete_command(receipt, *, certain) settles only that exact claimed record.
- Create agent/tests/test_lifecycle_dynamodb.py: Moto fixtures use dummy credentials,
  existing optional cloud requirements; no listening ports or actual EC2 calls.
- Update docs/cap04-lifecycle.md, checkpoint/handoff, sanitized dated evidence.
- Extend existing release assertion for module packaging; optional testextra excluded.

## Task 1: Durable wake/work/stop decisions

- [x] Write tests for exclusive initialization/reopen/missing identity, invitation
      atomic wake, one generation, readiness only after start acknowledgement,
      meaningful work vs background, drain/lease bounds and stale observation.
- [x] Observe missing-module RED. Implement strict complete record validation,
      bounded lease map and conditional whole-item CAS transactions. No retries.
- [x] Require new tests green without Moto skips; existing local lifecycle remains
      unchanged. No factory path may select the new adapter.

## Task 2: Durable command handoff and faults

- [x] Write RED tests for pending-only single claim, stale/mismatched/double receipt,
      pending expiry, claimed timeout, unknown completion, cleanup fencing and
      safe observed stopped/cooldown recovery.
- [x] Implement command state transitions exactly as spec, no external callback.
- [x] Add simultaneous CAS/drain-arrival and injected conflict/committed-lost-write
      tests, revocation-between-read/write, backward/nonfinite time/corruptstate and
      SDK policy mutation. Fix only reproduced failures with RED/GREEN.
- [x] Run remote/local invitation/lifecycle/inference allowance regressions.

## Task 3: Verify, review and hand off

- [x] Fresh review against spec and documented safety contract; resolve material
      findings with regressions. Preserve limitations as external-command handoff.
- [x] Run relevant release/build regression, repository lint/format, pip check,
      evidence hashes/privacy and diff whitespace checks.
- [x] Update docs/checkpoint/evidence with exact observed outputs, mark remaining
      HTTP/dispatcher/IAM/host integration/cloud acceptance explicitly pending.
- [x] Commit explicit local files; no push, merge, live deployment or gate closure.

## Execution ledger

Ruling: fixed one-item lease map is the smallest bounded serializable authority
for one demo host and128accepted requests; no global-table or scan implementation.
Ruling: uncertain commands remain locked rather than implementing an unjustified
automatic takeover. Actual EC2 cannot enforce the generation fence; a future
executor must own at most one claimed operation and prove termination/outcome.
The current component only provides the persistent protocol and tests it offline.

Execution rulings: explicit lifecycle initialization also atomically writes a
permanent lifecycle_identity marker in invitation metadata; deleting the host item
cannot reinitialize a command fence. Reproduced missing-state reset, inconsistent
ready-with-command, post-claim revocation and invalid renewal-token failures,
then fixed them with transaction/shape checks. Future activity/changed timestamps
were separately RED before bounded-time validation.

Fresh review reproduced unhealthy idle drain reopening admission. Added a RED
regression and a persisted strictly validated health flag; drain now preserves
health independently while accepted work may renew. Review clear, independent
39checks passed/no skips. A final malformed observation input regression observed
TypeError RED; explicit string validation maps it to fixed lifecycle refusal.
Full focused/release verification and exact result recording follow below.

Pre-flight: existing isolated worktree verified. Task1 host-row/metadata interfaces
feed Task2 command receipts under the same revision; no duplicate transaction-item
operations. Native Windows execution records TDD/results here without invoking
POSIX-only task wrappers. Existing base locks and active factories remain unchanged.

Final execution:40remote lifecycle cases included in139passed/no skips58.83s,
with a fresh built release proving module packaging. Independent review clear
following the reproduced unhealthy-drain fix;39checks independently passed before
the final malformed-observation validation. Repository lint/format, pip and
whitespace checks pass; base lock/local lifecycle/active factories unchanged.
Durable evidence: eval/evidence/cap06-remote-lifecycle-20261021.json. No real EC2,
AWS resources, model calls or HTTP/production activation. Commit locally only.
