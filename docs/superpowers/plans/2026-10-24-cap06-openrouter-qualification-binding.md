# OpenRouter qualification binding implementation plan

> **For agentic workers:** Use superpowers:executing-plans with TDD, independent audit support and one fresh final review. Owner approved implementation; continue without another execution-method approval.

**Goal:** Implement the approved explicit evidence binding while preserving default-closed host startup and all spending/deployment gates.

**Architecture:** Validate files once at startup and use a lightweight immutable in-memory verifier. Wire the actual verifier into the existing single-flight provider gate and recheck its proof after lifecycle awaits. Paired CLI inputs are the only production selection mechanism.

**Tech Stack:** Existing Python3.12/FastAPI/Uvicorn, standard library, existing BoundedIO and pytest. No new dependencies.

**Spec:** docs/superpowers/specs/2026-10-24-cap06-openrouter-qualification-binding-design.md, owner-approved24October2026.

## Global constraints

- Controlled Storefront only; no Step25/generalisation or PDF work.
- Existing OpenRouter Gemini3.5FlashLite, explicit selection, non-resettingUSD2cap; no real key/allowance access, new inference, initialization/enable/reset/refund or resource/public activation.
- Exact accepted-report/reconciliation hashes from the approved design. Source hashes are offline audit only; no20file runtime pin table.
- Binding<=16384bytes; report/reconciliation<=1MiB; duplicate-free exact fields; protected POSIX reader. UTC integer interval<=60days, issued<=now<expires.
- HostSettings v1/v2 remain unchanged; no-binding/default verifier remains false.
- Startup-only private hashing; no runtime file worker/reads. Captured immutable snapshot with in-memory expiry/client checks; provider1s/aggregate1.5s. No network in verifier.
- Preserve all uncertain charges and existing owner/identity/Confirmation/refresh/Action safety boundaries.

## Review focus

- Private evidence aliases another state/key file or changes during startup reads: refuse; Task1 metadata/alias tests.
- Minor source fix triggers brittle20file runtime refusal: source hashes stay offline; Task1 normal-release/rebinding regression.
- Guard/client/ledger mutated in memory while verification awaits: refuse; Task2 before/after identity tests.
- Captured qualification expires/closes during lifecycle wait: refuse before entry/output; Task3 await-fence tests.
- Qualification observation accidentally rereads files: injected reader becomes forbidden after startup; Tasks1/2 zero-I/O tests.

## Task1: Immutable private binding and provenance

**Files:** Create deploy/provider_binding.py and eval/tests/test_provider_binding.py.

**Interfaces:**

- configuration_fingerprint(settings:HostSettings)->str: canonical effective non-secret LLM settings, full inference mapping and contract identifier.
- candidate_binding(settings:HostSettings, \*, issued_at:int, expires_at:int)->bytes: synthetic-test/operator candidate bytes only, no write/approval/ledger operation.
- load_provider_binding(settings:HostSettings, path:Path, expected_sha256:str, \*, read_private=\_read_private, clock=time)->ProviderBinding: pre-SDK synchronous validation.
- ProviderBinding.snapshot()->BindingSnapshot: return captured startup evidence after an in-memory expiry check; never reread files. Initial private file validation remains in load_provider_binding.
- ProviderBinding.settings is the exact supplied HostSettings; binding/snapshot repr excludes private fingerprints and input paths.

- [ ] Write positive synthetic fixture with patched fixed test pins, actual existing v2 settings and retained allowance; missing module is RED. Assert no model construction, ledger mutation or key disclosure.
- [ ] Add malformed/duplicate/oversized/missing/digest/model/config/release/key/ledger/time/permission/link/alias/source-byte/metadata drift refusal tests. Assert exception has no cause/context or sensitive repr.
- [ ] Implement exact report/reconciliation pin constants, startup-only private proof loading, normal release verification and immutable snapshots; no source pin table. Evidence files are binding.parent/accepted-report.json and reconciliation.json; binding path explicitly selects that directory.
- [ ] Implement shared effective profile (OpenRouter timeout30, minimal/excluded reasoning, cap2, price ceilings and request/output bounds). Preparer returns bytes only; actual protected output installation remains external.
- [ ] Run pytest eval/tests/test_provider_binding.py -q; Expected: all pass. Ruff/format affected files; commit.

## Task2: Owned async qualification verifier

**Files:** Create deploy/provider_qualification.py and eval/tests/test_provider_qualification.py.

**Interfaces:**

- ProviderQualification(binding:ProviderBinding, guard:GuardedClient): bind exact real guard/OpenRouterClient/settings/ledger/prices/queue identities and values, without constructing a second guard/client.
- async observe()->QualificationProof|None; async recheck(proof:QualificationProof)->bool; async close()->None.
- Proof carries private owner token, immutable snapshot and validity; it cannot be reused across verifier instances. Public repr is fixed.
- Check actual guard bindings and captured snapshot/time; no I/O worker, network, evidence/key/source reads or allowance operations at runtime.

- [ ] RED missing module; test true synthetic observation/recheck, foreign proof, mutated delegate/settings/ledger/prices/queue, revoked/expired evidence and strict false on dependencies.
- [ ] Forbid all private-reader calls after startup; prove observe/recheck still work, disk changes apply only at the next startup, and expiry/closure/client mutation refuses.
- [ ] Implement actual client/effective settings binding and lightweight owned close state. Cancellation propagates, ordinary errors become None/false without logging raw details.
- [ ] Run both new modules' tests; Expected: all pass with zero fake provider POSTs/ledger changes. Ruff/format and commit.

## Task3: Explicit host wiring, proof freshness and CLI

**Files:** Modify deploy/host_bootstrap.py, deploy/host_agent.py and corresponding eval/tests/test_host_bootstrap.py/test_host_agent.py; add focused host binding fixtures/tests as needed.

**Interfaces:**

- create_host_app(..., qualification:ProviderBinding|None=None) retains existing parameters/defaults. Reject a simultaneous nondefault trusted provider_ready callback, wrong settings object or invalid binding before SDK creation.
- During readiness assembly, create one ProviderQualification against app.state.llm_client and bind its owned lifetime to \_ProviderGate. Late mismatch follows full current cleanup.
- \_ProviderGate.observe() returns a proof or strict legacy trusted True; ready() tests observation; recheck(proof) freshly verifies an owned proof, while legacy callbacks preserve existing test behavior. One-flight/time bounds and closed fences remain.
- \_QualifiedWork.check captures proof, awaits lifecycle check, then rechecks fresh owned proof and generation/failure/closure before returning.
- host_agent paired --qualification/--qualification-sha256; absent pair calls existing factory path unchanged. Present pair loads preflight binding before assembly; no env/bypass option.

- [ ] RED CLI partial-pair/default tests and qualified host/refusal/freshness/cleanup tests. Test actual typed clients with intercepted HTTP/SDK and synthetic private custody only.
- [ ] Implement two-stage startup, owner close and post-await in-memory proof revalidation. Verify expiration/closure during lifecycle wait and provider key wait cannot reach model POST/output; Stop/renewal stays independent.
- [ ] Run new binding/verifier tests plus host bootstrap/agent/openrouter/checks and affected inference/lifecycle/safety tests; Expected: all pass, default proof false, no actual inference.
- [ ] Run relevant source checks, commit source to enable genuine clean native capture.

## Task4: Native release, evidence and final review

**Files:** Extend eval/native_agent_probe.py and its tests, add docs/cap06-provider-qualification.md and eval/evidence/cap06-provider-qualification-20261024.json; update checkpoint/handoff/inert dossier and this ledger.

- [ ] Add native synthetic proof using real accepted report/reconciliation and actual20source files, fake protected key/retained ledger and read-only authority. Prove default false, explicitly bound qualification true, runtime expiry/closure and startup wrong-custody/evidence refusal and complete cleanup; zero model/AWS requests.
- [ ] Build new clean original native release under signed Python3.12.14/Node24.22.1, finite memory/CPU/time and Windows headroom guard; run Agent and independent archive roundtrip serially. Expected: exit0, immutable source/manifest and honestly synthetic qualification.
- [ ] Run focused/full relevant Python checks, source lint/format/pip and required TypeScript/build checks if packaging affected. Preserve earlier broad-suite exception; do not manufacture a full-green claim.
- [ ] One fresh whole-slice review; fix material findings with RED/GREEN regressions and focused suite. Record minor findings and all native limits/digests.
- [ ] Update operating guide/evidence/checkpoint/dossier; all real custody/capacity/apply/public flags remain false/null. Commit locally, leave worktree clean; no push/merge/deployment.

## Plan self-review

All approved sections map to Tasks1–4. Shared interfaces are named above; model source hashes remain an offline concern, per the owner amendment; no brittle source table is used in the runtime. Candidate-byte creation is deliberately not a real key-access/installation workflow. Two-stage validation resolves actual-client construction ordering. Cheap in-memory proof/expiry checks and owned close state are part of integration, not deferred correctness work.
