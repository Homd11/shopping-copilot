# CAP-07 Controlled Host & Application Acceptance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task in the current session after approval. Steps use checkbox syntax. The owner requested one consolidated cloud session; tasks below are preparation and ordered checks within that session, not separate cloud stages.

**Goal:** Accept the existing private Controlled Storefront host, including actual
custody/readiness, one reboot and bounded captured capacity, then leave it stopped
with no EIP.

**Architecture:** Prepare and freeze operator utilities and synthetic tests
locally. Execute one finite operation against the existing AL2023 host, adding
only its minimum DynamoDB authority and instance role; real-custody readiness and
captured-response capacity are distinct results inside the same session.

**Tech Stack:** systemd 252, nftables 1.0.4, Python 3.12.14/SQLite, Node 24.22.1,
Caddy 2.11.7, existing AWS CLI profile, DynamoDB, OpenRouter captured qualification.

**Spec:** [approved design](../specs/2026-10-26-cap07-controlled-host-acceptance-design.md)
and [exact allocation proposal](../../cap07-controlled-host-acceptance-proposal.md).
These documents are currently drafts; no task is executed by writing this plan.

## Global constraints

- Mandatory Free plan, USD 0 cash, Stockholm only, incremental AWS ceiling USD 0.25.
- T0 precedes first resource write; max 4 hours, teardown by 210 minutes, no reboot
  after 135 minutes, work ends by 160 minutes, normal stop/IP release by 180 minutes,
  one StartInstances and at most one controlled reboot.
- Existing native source023d9f6/artifact and runtime versions remain fixed.
- Existing key cap USD 2 non-resetting; preserve ledger UUID/history/uncertainty;
  proposed USD 0.10 readiness reserve; zero live model POSTs.
- Keep all public ports closed and DNS unchanged. No helper, extra disk, upgrade,
  source pinning expansion, per-request evidence hashing or public activation.
- The safety invariants and uncertain-Action recovery rules in AGENTS.md apply.

## Review focus

- Reboot crosses the deadline: startup refuses; watchdog still stops/releases.
- Duplicate/conflicting receipt or interrupted handoff: no reset/double counting
  and no second enabled writer.
- Model budget sufficient for readiness but network forbidden: signed readiness
  is real, no provider POST escapes, capture cannot read canonical custody.
- Metadata rule failure and boot ordering: no app starts before both barriers.
- Mid-session disconnect/usage pause/OOM: finite teardown wins over another test.

## Files and interfaces

Existing runtime files are reference inputs, not behavior changes:
`deploy/{host_agent,host_bootstrap,provider_binding,host_checks,host_metadata}.py`,
the six `deploy/shopping-copilot-*` units, `deploy/Caddyfile`,
`agent/{admission,lifecycle,inference}` and the retained native artifact.

After design approval, create focused operator-only preparation code:

- `deploy/custody_handoff.py`: strict offline single-writer ledger migration.
  Interface `prepare_handoff(source: Path, manifest: Path, destination: Path) -> dict`;
  manifest contains the explicit allocation, source backups, exact receipt map
  and upward-rounded provider status snapshot. Return only sanitized counts and
  fingerprints safe for the private operation; no network/provider activation.
  Existing destination requires exact verified idempotent match or refusal.
- `eval/tests/test_custody_handoff.py`: synthetic SQLite/history/cap tests.
- `eval/cap07_host_acceptance.py`: bounded private HTTP/SSE/capture driver and
  sanitized metrics. Interface `run(profile: Path, receipt: Path) -> int` with
  strict `control`/`captured` modes, explicit private-CA trust and immutable
  resource limits. Never auto-select a live model or discover keys from dotenv.
- `eval/tests/test_cap07_host_acceptance.py`: fake SDK/HTTP/clock/SQLite fixtures
  for operation ordering, time/request bounds, no-key capture and failure exits.
- `.scratch/cap07-controlled-host-preparation/`: frozen guest unit drop-ins,
  nft batch, deadline guard, custody manifests, private TLS recipe and detached
  PowerShell operation/watchdog payloads. These are operator artifacts outside
  the immutable application release, not public credentials or generated product.
- `.scratch/cap07-controlled-host-execution/<new-operation-id>/`: immutable phase
  receipts, private backups/state and final file manifest. Never mutate the
  previous provisioning operation or resume its grant/state file.
- `docs/cap07-controlled-host-acceptance-results.md`,
  `eval/evidence/cap07-controlled-host-acceptance-<execution-date>.json`,
  `PROJECT_CHECKPOINT.md`, `handoff.md`: actual results only after execution.

### Task 1: Freeze local operator preparation before any AWS session

- [ ] Write failing synthetic tests for228 deduplicated settled rows,19uncertain
      holds, unchanged shared UUID and per-row values, provider-gap hold,
      `B+0.10<=2`, insufficient remaining, changed cap, duplicate conflict,
      untrusted/missing source, existing target mismatch, interrupted copy and
      disabled source/canonical single-writer transition. No live key/database.
- [ ] Run `python -m pytest eval/tests/test_custody_handoff.py -q`; verify the new
      tests fail because the operator helper is absent, then implement only its
      specified migration contract and rerun to pass. No new runtime grant API.
- [ ] Write/run failing driver tests for no model endpoint in control mode,
      capture key/ledger isolation, exact1/5/8 queue outcomes, unknown mutation
      reconciliation, deadline across reboot, expired startup, missing watchdog,
      metadata/barrier failure, TLS verification and stop/release on pause/OOM.
      Include generation 0 fixture isolation, just-in-time300-second real startup
      and a real-clock3600-second idle/5-second drain after off-host stop, simulated
      with an injected test clock only in local fixtures, never production.
      Implement the bounded driver and freeze guest/operator payloads; rerun green.
- [ ] Rehearse real TLS and HTTP/SSE with synthetic custody/SDK, identical unit
      constraints and the fixed 0.4-second captured response. Prove <=300 requests,
      <=10 minutes/lane, <=10 seconds/cohort, zero real SDK/model calls, no leaked
      tasks/leases and no canonical file reads by capture. Confirm estimated
      DDBunits/transfer fit proposal bounds using conservative size rounding.
- [ ] Review startup-only binding behavior against existing provider-binding
      tests. Render/verify systemd 252 units, fixed-deadline guards, narrow IAM,
      metadata and endpoint-only egress batches offline. Preserve negative tests
      for off-origin/sensitive-field/Confirmation/stale/duplicate/refresh safety.
- [ ] Run relevant focused pytest, Ruff, repository format/lint/tests/build for
      changed code. Freeze hashes and receipt schema; leave app runtime/release
      unchanged. If a runtime bug is found, resolve/review locally and update the
      artifact proposal before AWS, not through another exploratory cloud boot.
- [ ] Confirm the owner has approved the consolidated design and exact resource/
      cost/custody/readiness reserve scope. Do not infer an allocation from this
      document or reuse the preceding completed grant.

### Task 2: Enter the single session and establish isolation (T0 to75 minutes)

- [ ] Refresh official public rates and read account/Freeplan/credits/current
      resource state. Confirm stopped exact host/root, CPUStandard, SG22only,
      current operator IPv4/32, key cap/history and sole writer; no upgrade.
      Quiesce local key consumers and capture the one approved key-status GET
      now; retain its protected snapshot without another GET at handoff.
      Preflight expiry is48 hours from approval. Freeze exact names/IDs in a new
      operation; arm detached durable stop/release watchdog before resource writes.
- [ ] Record T0 and fixed end/teardown/reboot deadlines. Create/verify the one
      table/namespace and narrow role/profile, associate it, initialize authority
      once under operator identity and record private identities. Reconcile any
      unknown write before progressing; no blind create or Start retry.
- [ ] Start the original once, allocate/associate one EIP, verify retained SSH
      trust. Install/verify the fixed acceptance timer and startup deadline guard
      before retiring the 90 minute timer; old expired units stay masked.
- [ ] Install protected configuration, catalogue and service identities; enable
      metadata plus endpoint-only egress and verify actual allow/deny probes.
      Keep all80/443SG ingress closed. No real key/ledger enablement yet.
- [ ] Enable bounded persistent journal; use short harmless fixture commands
      with the component units' exact sandbox properties for denial checks.
      Keep actual Agent/host target stopped and lifecycle generation 0 until
      real custody, TLS and startup configuration are ready. Verify UIDs/cgroups,
      root-owned release, private catalogue/WAL access and bounded logs. Prove
      metadata failure blocks app startup before lifespan; restore barriers and
      remove fixture overrides without advancing actual lifecycle authority.

### Task 3: Install actual custody and prove signed readiness (by 105 minutes)

- [ ] Confirm local consumers stayed quiescent; snapshot/validate source ledgers/
      receipts against the retained single key-status GET. Prepare canonical shared-UUID ledger with exact
      imports/gap hold/explicit USD 0.10 reserve. Retire active local key paths and
      disabled alternative writers; keep protected rollback backups.
- [ ] Install owner-only canonical custody, unchanged accepted report and
      reconciliation, hostv2config, bounded-expiry binding and independent SHA pin.
      Verify destination bytes/history, startup binding and actual GuardedClient.
      Enable ledger only after confirmed model-network denial.
- [ ] Install loopback 443/private-CA Caddy override and managed hosts block;
      preserve proxy capabilities and route protections. Verify real TLS with
      explicit CA and hostname/SNI checks, no global trust or publicACME.
- [ ] Only now call manual_start/claim, acknowledge the already observed running
      designated host without a second Start, and immediately start the real
      target. Inside300-seconds, use fresh signed readiness for release/generation and
      reconcile healthy conditionally. Verify wrong/unsigned/stale proofs refuse,
      all five real checks pass and the canonical ledger has no new attempt.

### Task 4: Exactly one reboot and bounded capacity (by 160 minutes)

- [ ] Before135 minutes, close sessions/leases and mark real lifecycle unhealthy;
      retain generation, enabled units, authority IDs and ledger. Request one
      guest reboot, capture distinct boot IDs, reconnect without another Start.
- [ ] Before any manual service intervention, verify automatic swap/swappiness,
      journal continuity, both nft barriers before all application units, correct
      PIDs/UID/cap/limits, same private custody and real signed readiness. Failure
      means teardown, not a second reboot or hand-started persistence "pass".
- [ ] Run the bounded real-custody control lane and sample whole-host metrics.
      Stop on thresholds from the design; record all refusals and no model POST.
- [ ] Stop only the real Agent, start isolated captured launcher with fake
      custody, same sandbox/limits and actual Store/proxy/DDB. Run fixed 1/5/8
      captured HTTP/SSE cohorts, preserve overload accounting and network denial.
      End capture, restore real Agent, verify canonical ledger unchanged and
      obtain a final fresh real-custody signed readiness proof.

### Task 5: Stop/IP release by 180 minutes; finish authority/evidence by 240 minutes

- [ ] By160 minutes or on earlier completion/failure/pause, close streams/drain
      work, revoke both lane invitations, record last meaningful activity,
      stop capture, disable
      and back up canonical ledger consistently. Disable app target/components,
      restore safe relative 90 minute guard, remove temporary TLS/hosts/acceptance
      overrides after startup is disabled; retain protected custody and history.
- [ ] Stop original and observe stopped; disassociate/release exact EIP and
      observe no publicIP/no operation EIP by T0+4 hours. SSH failure never delays
      API teardown. Leave original root/table/role/profile retained as proposed.
- [ ] With host stopped/IP released, do offline receipt work until last activity
      plus3600 seconds. Reconcile observed stopped state to draining, wait5 seconds,
      reconcile to pending stop, claim, freshly observe exact host already stopped,
      acknowledge without another EC2 mutation and reconcile stopped. Keep the
      same generation. Deadline/pause/uncertain failure instead records exact
      non-admitting authority state; never edit rows/clock to invent stopped.
      Preserve unknown command/Action/reservation outcomes as unresolved. Verify
      no extra compute/poller was created; retrieve private receipts securely.
- [ ] Write gate matrix and bounded actual cost/time/request/resource evidence,
      including skipped/failed gates. Update checkpoint/handoff with the true
      frontier. Record interpreter adoption only on full actual host acceptance;
      public wake/DNS/ACME/browser/live-provider gates remain explicitly open.
- [ ] Verify document/evidence consistency and redaction, commit local results;
      do not push, merge, publish or automatically start a deployment stage.
