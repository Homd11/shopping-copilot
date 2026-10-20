# CAP-05 access and single diagnostic preparation

**Scope:** Continue the owner-approved access/qualification frontier. Read-only
access is authorized; inference requires a separately approved concrete allowance.
No deployment, plan upgrade, active model switch or browser Actions.

The owner opened ordinary CloudShell and returned all four positive availability
statuses. A signed current-user AWS CLI 2.38.2 installation and browser-approved
`cap05-stockholm` login now permit the local SDK's same read-only check; it also
returns AUTHORIZED/AVAILABLE/AVAILABLE/AVAILABLE. SDK login requires the pinned
CRT extra, awscrt0.36.0. No access keys were collected or model calls made.

## Single diagnostic design

Prepare a fixed `ar-01` request from the existing exposed intent corpus, current
intent-v32 prompt/schema9, model openai.gpt-oss-20b-1:0, eu-north-1, temperature0,
1536 output tokens, one Converse attempt and zero automatic retries. Pin the
request/corpus hashes before seeking approval. Default execution prints the plan
only and does not resolve credentials or create a spending ledger.

After explicit owner approval of at most USD0.02 additional AWS credit use for
this diagnostic only, require a nonempty approval reference and an exclusive
claim in the fixed report directory. Initialize a USD0.02 ledger once, reserve
USD0.015 before the only model call, retain it after success/failure/cancellation
and never reset/reuse the claim. The conservative full-model list-price bound
is USD0.01409024 for128Kinput/16Koutput; no prompt caching or extra services are
requested. This is a dated conditional price bound, not an invoice or AWS cash cap.

Record model/configuration, hashes, latency, safe failure category and normalized
usage. Keep monetary cost unknown and distinguish a token-based estimate from
verified charges. The response can be checked locally with existing corpus scoring
through a scripted provider; no repair may make another real call. No claim of
qualification from one case. Stop after this attempt and inspect before proposing
a full set. The frozen104attempt strict benchmark needs a separate budget and
runner; the old Gemini/OpenRouter run approvals cannot authorize it.

## Steps and verification

- [x] Confirm owner CloudShell and local SDK eligibility without inference.
- [x] Write failing tests for dry-run/no-client construction, exclusive claim,
      reserve-before-call, failures/cancellation keeping charges and exact binding.
- [x] Implement eval/bedrock_diagnostic.py using existing ledger and client seams.
- [x] Run focused diagnostic/adapter/ledger tests, formatting/lint and independent
      review. No runtime application change warrants repeating all browser tests;
      retain the earlier754/1timeout plus three successful reruns transparently.
- [x] Record sanitized access proof, prepared plan and local tooling provenance;
      keep login tokens/cache/log URLs out of committed evidence. Commit locally.
- [ ] Request USD0.02 authorization only after the exact diagnostic is reviewable.
- [ ] If approved, run at most one attempt; otherwise leave execution pending.

Base:8ac2304. This small evaluation utility is an implementation choice within the
existing qualification workflow; it does not change product behavior or relax
CAP-05's full strict/unseen requirements.

Execution evidence: default collection RED for missing module; seven initial tests
GREEN. Independent review found actual request reconstructed after SDK initialization
was not rechecked against its fingerprint. Added a mutation-during-login regression,
observed RED with one unintended fake entry, then GREEN with zero entries. Common
request_hash is now checked immediately before complete; reservation remains held.
Eight diagnostic tests and75combined provider/ledger/benchmark/budget checks pass.
Independent Spec/safety recheck and Standards clear. No model invocation executed.

The current-owner installed/sign-in evidence supersedes research-only earlier
CRTabsence/local-authunknown text. Additional requirement file pins the SDK CRT
extra; base lock unchanged. No credentials or auth URLs enter committed evidence.
Source preparation and budget approval follow; only the one request is proposed.
