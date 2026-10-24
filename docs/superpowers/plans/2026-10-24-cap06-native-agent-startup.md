# Native Agent startup verification plan

> **For agentic workers:** Use superpowers:executing-plans with TDD and one final fresh review. This continues the authorized native host preparation.

**Goal:** Exercise the packaged Agent's real Linux Uvicorn startup, signed closed
readiness and graceful shutdown with synthetic external authority.

**Architecture:** Reuse the verified native release archive, exact28runtime wheels
and retained native Node binary. Keep production code unchanged. Inject a bounded
read-only Dynamo authority through the existing sdk_factory seam; use the actual
OpenRouter client with a synthetic key and the unchanged unqualified provider gate.

**Spec:** Existing CAP06 host-bootstrap/launcher/checks designs and the newest
PROJECT_CHECKPOINT.md. The owner requested resuming the host work; these are
verification details within that approved scope, not a new deployment design.

## Constraints and review focus

- Controlled Storefront only; Step25 remains parked and unmerged.
- No AWS/real SDK request, real key/allowance, provider request, new spending,
  service installation/systemd activation, public HTTPS/DNS, push or merge.
- Retained official image; non-root, network-none, read-only root, finite CPU,
  RAM/PID/tmpfs/deadline limits, no owner home/checkout/credentials/socket mounts.
- Only the existing external-authority seam is injected. Actual release root,
  protected POSIX settings reader, model factory, Uvicorn and lifespan stay real.
- Default provider readiness stays false. An enabled synthetic allowance with an
  existing uncertain reservation tests that this gate independently blocks work.
- Observe individual checks inside the real lifespan without replacing them or
  setting ready=true. Reject forbidden datastore operations and external sockets.
- Label the proof as synthetic authority: it does not establish actual AWS access,
  qualified readiness/capacity, production interpreter/security, systemd or reboot.

## Task1: Native proof and bounded synthetic authority

Files: eval/native_agent_probe.py, eval/tests/test_native_agent_probe.py; ignored
orchestrator/receipts; versioned guide/evidence and checkpoint/handoff.

- [x] RED: test actual Dynamo store/lifecycle consumption of the bounded read-only
      double, isolated returned rows, invalid reads, closed client and generation0.
- [x] Implement the double and probe; GREEN focused tests.
- [x] Verify/extract the original archive unchanged; install28runtime wheels
      offline with hashes. Run actual native Storefront and Agent on loopback.
- [x] Require ordinary HTTP availability; signed ready=false with response MAC and
      no-store, invalid proof403, four concrete checks true/provider false, no
      provider metadata/charges/external connection/control mutation.
- [x] SIGTERM must exit cleanly within the bound and close owned resources once.
      Separate generation0 startup must refuse with fixed redacted error and clean
      every constructed resource. Preserve catalogue, ledger and manifest digests.
- [x] Fresh whole-slice review; focused host compatibility, source lint/format and
      relevant checks. Production/TS code unchanged; retain previous full-suite
      results and browser-cleanup exception rather than repeating unrelated suites.
- [x] Record exact source/archive/probe/runtime digests and limits; commit locally.

**Expected:** New protocol tests pass; actual native proof returns verified startup,
closed signed readiness, graceful shutdown and invalid-generation refusal. Actual
remote authority/provider qualification and real-host acceptance remain open.

Ruling: Uvicorn0.35 re-raises SIGTERM after graceful lifespan cleanup; actual exit-15 is accepted only with completed cleanup audits and no patched signal handler. The retained first two runs exposed header-case and unauthenticated-status harness errors, corrected without changing production guards. Final full native proof passes; controlled timeout removal passes;71focused host checks pass.
