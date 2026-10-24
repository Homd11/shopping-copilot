# Native Linux release and explicit provider preparation plan

> **For agentic workers:** Use superpowers:executing-plans with TDD and one final fresh review. Continue the owner's authorized host preparation; no deployment or provider calls.

**Goal:** Build an unmodified production-origin release from a clean genuine Git
checkout in Linux, and support the approved OpenRouter choice in protected host
configuration while keeping model readiness closed.

**Architecture:** Keep native Python/Node/Caddy services and the existing release
builder. Prepare a shallow credential-free Git object snapshot, pinned native Git,
Node/pnpm and a verified project-only cache for a network-none build. Add strict
host configuration v2 for the approved OpenRouter provider; retain Bedrock v1.

**Tech stack:** Existing Python3.12/Linux runtime lock, Node24.13.0, pnpm11.19.0,
retained AL2023 image, supplier-signed Git2.50.1 build tool, pytest and Docker.

**Spec:** Existing CAP06 host design/launcher/isolation contracts, latest
PROJECT_CHECKPOINT.md, the owner's24October OpenRouter fallback approval and
explicit request to continue the native-release/host-configuration step.

## Constraints and review focus

- Controlled Storefront only; generalisation/Step25 remains parked and unmerged.
- No AWS/account/provider API, actual key/allowance migration, model spending,
  service installation, host-user changes, public TLS/DNS, deploy or push.
- Existing non-resettingUSD2cap, unknown-charge holds, admission, concurrency,
  Confirmation and uncertain-outcome non-replay remain binding.
- V2 accepts only openrouter/google/gemini-3.5-flash-lite and a bounded protected
  Agent-only provider key file; no ambient selector, plaintext key JSON or cap knob.
- V1 remains exact Bedrock-compatible. Neither config version grants readiness;
  the default provider verifier remains false and audio remains guarded.
- Native source must retain actual original Git commit/tree and clean status;
  owner config/credentials/history/hooks and ignored files do not enter the input.
- Source extraction and output publication must reject traversal, links,
  overwrite and incomplete/unbound input; no provenance stub or manifest rewriting.
- Git package acquisition is public, pinned to the image's repository release,
  hash/signature checked, extracted only; not host package/security approval.
- Native checkout/build/runtime use bounded disposable network-none Linux storage,
  no owner checkout/home/credentials/socket mounts or published ports.

## Task1: Explicit protected provider configuration

Files: deploy/host_config.py, eval/tests/test_host_openrouter.py and the existing
host bootstrap regression.

- [x] Observe RED v2 config cases, implement exact schema/provider/model/key file
      loading with immutable/redacted settings and literal2.00provider ceiling.
- [x] Test invalid schema/provider/model/type/keys/paths, exact price binding,
      retained ledger uncertainty and no provider construction/ledger initialization.
- [x] Extend existing app seam for both provider selections; verify closed signed
      readiness, admission/Stop behaviour, no model calls/charges and speech refusal.
- [x] Run complete host compatibility and broader regressions; record transient
      Node fixture startup failure and successful unchanged isolated recheck.

## Task2: Genuine clean native build

Files: eval/native_release_source.py, its tests, eval/native_release_probe.py and
versioned evidence/guide. Keep acquired tools, caches and source inputs ignored.

- [x] Observe RED source-snapshot tests, implement a bounded deterministic ZIP of
      actual shallow Git objects with exact commit/tree and no owner configuration.
- [x] Verify pinned Git RPM against published metadata and pinned-image public key;
      extract selected binary/licence only; prove version and actual DSO availability.
- [x] Stage only359locked pnpm entries and6333verified content paths; preserve the
      original cache and exclude projects/configuration/symlinks/credentials.
- [x] Commit reviewed source first, capture that exact clean revision, and run
      real native Git checkout/fsck/status, frozen offline install and unmodified
      production build with retained source commit/tree and artifact digest.
- [x] Exercise the actual native release/runtime with synthetic private state,
      default POSIX v2 key refusals, native Storefront restart/auth/persistence and
      Agent running-loop refusal only. Full native Agent startup/readiness remains
      open. No SDK/provider/ACME execution or manifest adaptation.

## Task3: Verification and current frontier

- [x] Fresh whole-slice review; fix material issues with targeted RED/GREEN checks.
- [x] Run source format/lint/build/TypeScript tests and full Python Agent/Evaluation
      suites sequentially, in separate processes, after Docker proof cleanup.
      This preserves coverage while reducing local peak allocation after the
      prior combined-run MemoryError; retain every failure and exact rerun result.
- [x] Record native/source/toolchain/runtime digests, key privacy/authority and
      proof limits; update checkpoint/handoff/apply dossier and commit locally.

Still open afterward: production interpreter/AMI/package security adoption,
actual host provisioning/systemd boot/reboot/capability/metadata/log acceptance,
full Agent qualified readiness/capacity, remaining key allowance custody and exact
account/cost/resource/rollback approvals, then cloud desktop/Android acceptance.

Verification exception retained: complete Agent899passed; Evaluation546passed,2warnings,1Browser.close response-disposal failure in unchanged milestone harness. Whole affected module passes unchanged on recheck1test/12.78s. No uninterrupted full-green claim or product workaround. See eval/evidence/cap06-native-release-openrouter-20261024.json.
