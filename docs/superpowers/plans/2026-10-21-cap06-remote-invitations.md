# Remote invitation adapter implementation plan

> **For agentic workers:** Use superpowers:executing-plans for inline local
> implementation and a fresh final review. No cloud resources or active backend
> selection are authorized by this plan.

**Goal:** Implement and test the first remote authority component: the existing
invitation contract backed by atomic DynamoDB transactions.

**Architecture:** A low-level injected client operates an explicitly initialized
namespace in an existing pk/sk table. Strong reads and conditioned transactions
preserve quota/grant invariants; no table/runtime initialization or retry on
uncertain writes. Existing SQLite selection remains unchanged.

**Tech stack:** Python3.12, pinned existing Boto3, optional Moto5.2.4 DynamoDB
emulation, pytest. No running Docker, Java installation, cloud or paid requests.

**Spec:** docs/superpowers/specs/2026-10-21-cap06-remote-invitations.md. API evidence:
docs/research/2026-10-21-cap06-dynamodb-invitation-contract.md. Base:8eb1bc4.

## Global constraints

- All spec bounds hold:31days/20redemptions/100sessions/1000invitations,
  start inclusive/end exclusive,192-bit codes, SHA256-only persisted identities.
- SDK Region eu-north-1, normal HTTPS endpoint, connect/read at most5/15seconds,
  total_max_attempts=1. Each transaction has one unique32-character request token.
- No active admission/lifecycle factory or provider changes. No AWS table/API,
  credentials, inference, DNS, resource, certificate, upgrade or push action.
- Preserve irreversible cumulative counters and revocation; no TTL/delete/reset.
- Never expose codes, subject/hash records, raw service errors or credentials.

## Review focus

1. Final-slot races must condition counter consumption and the same grant binding
   atomically; independently read values are insufficient.
2. Missing metadata with existing namespace rows must not permit reinitialization.
3. A committed write followed by a lost response must be refused once without
   replay, refund, new identity or false success.
4. Expiry while the SDK request is in flight must refuse the returning grant or
   allocation, retaining any committed usage.
5. Emulator success does not qualify AWS conflicts/IAM/durability; inject errors,
   pin request semantics and keep actual host integration gated.

## Files and interfaces

- Create agent/admission/dynamodb.py: `DynamoInvitationStore`, matching issue,
  redeem, allowed, allocate_session, wake_invitation, valid_invitation, revoke and
  sanitized status. No import-time SDK factory. Constructor parameters are client, table, namespace, identity and optional clock;
  construction performs read-only identity validation;
  explicit `initialize(client, table, namespace)` returns a new identity and
  refuses nonempty namespaces. Use only the approved initialized schema1.
- Create agent/tests/test_admission_dynamodb.py: real mocked Boto3 DynamoDB request
  path and conditional transaction tests, dummy credentials only. No real endpoint
  traffic, local listeners or credential-chain resolution. Missing optional Moto
  is an explicit skip; the recorded verification must install it and run no skips.
- Create eval/requirements-cloud.txt: optional pinned emulation dependencies,
  separate from base runtime lock. Install under existing locked requirements.
- Update docs/cap04-invited-access.md, checkpoint/handoff and sanitized evidence.

## Task 1: Atomic invitation contract

- [x] Pin/install optional Moto5.2.4; retain existing SDK/base dependency pins and
      run pip check. Installation prepares offline testing, not cloud resources.
- [x] Write tests before implementation: exact windows/revocation and quota reopen,
      idempotent redemption, nonrefunded replacement, wake separate from shopping,
      metadata identity/missing/corrupt state,1000-capacity and exclusive initialize.
- [x] Observe missing-module RED with `python -m pytest agent/tests/test_admission_dynamodb.py -q`.
- [x] Implement strict received/input validation, key/value encoding, strong reads
      and the bounded three/four-item transactions described by the spec. Status
      uses bounded consistent prefix queries. No active configuration changes.
- [x] Run the new suite and existing admission store/HTTP/limits/model boundaries;
      require green and no emulator skips.

## Task 2: Race, ambiguity and SDK-contract checks

- [x] Add RED tests for concurrent final redemption/session claims, stale grant
      binding, revoke-between-read/write, expire-during-write, committed-but-lost
      response, provider denial, bad clock/record, stale namespace and query bounds.
- [x] Inject failures on the real client method seam, assert at most one attempted
      transaction and no replay/refund/secret exposure. Instrument all reads and
      writes to require ConsistentRead and conditioned metadata/identity checks.
- [x] Make minimal fixes, run the new tests and all existing lifecycle/admission/
      allowance regressions. Verify every changed safety invariant at this seam.

## Task 3: Review, verification and handoff

- [x] Run repository relevant lint/format and build checks; runtime package includes
      this module through the existing allowlist, optional emulator stays outside.
- [x] Fresh-context review against spec and standards; fix material findings with
      RED/GREEN. Record limitations without claiming real AWS acceptance.
- [x] Document this component as disconnected from active configuration, record
      results/checkpoint, commit explicit files locally, no push.

## Execution ledger

Owner's explicit continuation covers local implementation of the approved cloud
control architecture. No additional feature or account authorization is inferred.
Implement inline in the existing linked worktree. Requests for another permission
round would repeat the authorization already supplied.

Ruling: DynamoDB Local cannot run under the available Java8 and Docker is stopped;
use optional pinned in-process Moto rather than starting unrelated host services.
PyPI metadata checked21October: Moto5.2.4/Python>=3.10; DynamoDB extras include
py-partiql-parser0.6.3. Preserve emulator/real-service limits in evidence.

Execution evidence: missing-module RED before code. The initial emulator failure
was traced to adjacent condition/update strings merging an expression alias;
adding a separator restored correct request aliases. Three safety regressions
observed RED before fixing boolean schema acceptance, post-commit revocation
revalidation and validated-limit binding; four SDK-bound regressions observed RED
before strict retry/timeout validation. Fresh reviewer reproduced a malformed
status-row bug; its new regression observed RED, then GREEN after status validated
the actual queried row through a shared validator. Review recheck clear.

Final new adapter40tests pass with no skips. Final focused admission/lifecycle/
allowance plus fresh artifact build:99passed/no skips in39.96s. Prior full release/
proxy subset14passed in148.42s before the final status-only fix; the final build
and focused checks use that fix. Optional dependencies/pip check clean; no base
lock change. Preserve scope: no active factory, AWS calls, table creation, model
calls, DNS, provider switch or public deployment. Next component is remote
lifecycle arbitration and safe command fencing, followed by host integration.
