# CAP-04 cloud readiness: implementation tickets

**Status:** ready-for-agent — approved scope, published to the local tracker.

Source: approved 11 October design, accompanying specification and availability decisions, amended on 14 October for the owner-provided `scpilot.tech` domain.
See [layout evidence](research/2026-10-14-cap04-sibling-hostnames.md) and [HTTPS preparation](cap04-domain-https-plan.md).
The parent CAP-04 ticket remains unchanged. Numbers are local to this feature.
Independent tickets may start at the frontier; this does not authorize parallel
agents or any external actions. Account facts and provisioning permissions are
separate from ticket-to-ticket blockers.

## 01 — Prove separate-origin Shopper identity through HTTPS

**What to build:** A disposable browser/proxy rehearsal comparing unrelated sites with approved sibling HTTPS hostnames while third-party cookies are blocked.

**Status:** resolved for desktop layout feasibility. Android hardware and deployed-domain acceptance remain in 08/CAP-07. The unrelated-site result remains negative; no cookie-only fix is claimed.

**Blocked by:** None — can start immediately.

- [x] Reuse the current linked Shopper journey with a scripted provider, valid HTTPS in both layouts and a genuine cross-site negative control; report browser versions and privacy settings.
- [x] Demonstrate two-browser cart isolation, linking, refresh, two tabs, opening a product, add, Confirmation/Undo and SSE reconnection without repeated Actions.
- [x] Investigate partitioned embedded authority without disabling privacy, CSRF, ownership or source-window validation; distinguish embedded and top-level storage behavior.
- [x] Record a supported configuration or an explicit negative result. Keep probe changes disposable; do not silently adopt an unsuccessful topology.

## 02 — Establish account and complete network-cost feasibility

**What to build:** A reviewable choice of eligible ingress, egress and hosting that can provide the public demo within available credits without upgrading the AWS account.

**Blocked by:** None — can investigate alongside 01.

- [ ] Reconcile owner-provided current plan, credits, expiry, service/model access and regional evidence; never fabricate entitlement or use first inference as a read-only access test.
- [ ] Compare custom-domain CloudFront private/public origins and direct EC2 HTTPS with the documented alternatives, including model access, deployment artifacts, administration and maintenance egress.
- [ ] Produce the complete two-month bill of materials, traffic/token assumptions, qualification allocation and contingency; distinguish reference estimates from a quote. Compare manual startup with optional Lambda startup, counting the public waiting page, control storage, logging, abuse traffic, EBS and retained IPv4 costs; separate stopped hours from running hours.
- [ ] Verify Free-plan eligibility for every wake/control service and avoid a standing server or mandatory NAT gateway solely for wake. Select manual startup if automatic wake is ineligible or breaks the credit-only envelope.
- [ ] Explicitly exclude unavailable flat-rate plans and automatic paid upgrades. Mark unavailable account evidence as an external blocker, not a passing gate.
- [ ] Make no resources, purchases, subscription acceptances or model calls. A feasible network choice remains conditional on the browser result from 01 and is reconciled in 09.

## 03 — Run a Shopper journey through production origin configuration

**What to build:** The existing shopping journey works locally through the production-style HTTPS proxy with configurable public origins and private service routing.

**Status:** resolved for local production-style routing on 14 October.
See [implementation evidence](research/2026-10-14-cap04-production-origins.md) and
[operating instructions](../deploy/README.md). Public AWS/domain and Android
qualification remain separate gates.

**Blocked by:** 01 — successful browser feasibility result (resolved).

- [x] Carry the successful sibling-hostname configuration (`app.scpilot.tech` / `store.scpilot.tech`) into the actual services; serve built assets without development reloaders and keep application ports on loopback.
- [x] Preserve exact public origin and iframe source checks, authenticated private reads, CSRF, cookies and current Action safety across browse, add and guarded confirmation.
- [x] Show isolation with two browser contexts; malformed origin/host configuration fails clearly and no browser input selects an arbitrary private destination.
- [x] Demonstrate SSE initial delivery, heartbeat, cursor reconnect and Stop through the proxy; personal responses and Set-Cookie never cross cache/user boundaries.
- [x] Public mode excludes test/reset endpoints. This local runtime configuration does not claim CloudFront or AWS deployment qualification.

## 04 — Admit invited Shoppers with bounded public usage

**What to build:** An invited Shopper can enter and use the demo while expired, revoked or excess access receives a clear response before model work.

**Blocked by:** 03 — production origin journey.

- [ ] Issue a separate code for each tester with explicit absolute testing-window bounds, independent revocation and finite redemption/session limits; exchange secrets without URLs/logging and preserve existing Shopper ownership after admission. Restart never renews validity. Browsing may be public while running; AI use requires admission.
- [ ] Enforce admission for session creation, follow-ups, events and action-result routes; an invitation never grants access to another Shopper's session.
- [ ] Enforce finite configurable request size/rate, active-session and queue limits, including global limits that new cookies cannot bypass.
- [ ] Show understandable expired-access and busy states without submitting duplicate requests or evicting another active Shopper.
- [ ] Verify abuse and isolation at the browser/HTTP boundary using the scripted provider; do not rely on client-only controls or IP addresses as identity.

## 05 — Enforce a durable inference allowance across failures

**What to build:** The Agent admits a model request only when a durable global allowance covers it and keeps that protection through crashes, retries and restarts.

**Blocked by:** None — existing Agent request/provider seams support independent local work.

- [ ] Reserve a conservative cost atomically before interpretation, advice and repair requests; use a deterministic fake provider and explicit test prices.
- [ ] Reconcile known costs once, retain uncertain reservations and refuse further requests when allowance cannot cover them. Concurrent callers cannot over-reserve.
- [ ] Interrupted requests, duplicate settlement and process restart never replenish allowance; corrupt/missing initialized storage disables inference rather than resetting it.
- [ ] A persistent kill switch and finite queue/concurrency bounds prevent new model calls and expose a clear application state; no automatic provider fallback.
- [ ] Read-only/full storage produces safe refusal. Keep runtime policy provider-neutral and leave Bedrock-specific adapter/price verification to CAP-05; preserve existing provider caps.

## 06 — Rehearse release, catalogue restore and safe restart

**What to build:** A local release can be installed, restarted and rolled back while preserving the catalogue and spending history and applying the documented Shopper reset behavior.

**Blocked by:** 03 — production origin journey; 05 — durable allowance.

- [ ] Exercise built releases with external persistent catalogue/configuration/ledger storage and restricted service permissions; schema incompatibility prevents serving.
- [ ] Prove Agent-only restart retains the surviving Storefront cart while invalidating Agent authority; Storefront-only restart resets commerce and requires fresh linking.
- [ ] In both restart directions, old ActionResult/Confirmation/Undo authority cannot apply to a new state and no uncertain Action is replayed.
- [ ] Restore a consistent catalogue backup into a disposable copy and check revision/content. Rollback never restores an older allowance balance.
- [ ] Demonstrate bounded redacted logs, failed health checks and disk failure. Record release/rollback/teardown procedures without executing cloud teardown or modifying shared resources.

## 07 — Wake invited Shoppers and stop safely when idle

**What to build:** An invited Shopper can reach a waiting page, start a stopped demo and enter when ready; the demo stops safely after 60 minutes without genuine work, with manual owner startup as fallback.

**Blocked by:** 04 — admission; 06 — release/recovery.

- [ ] Rehearse the full waiting-page-to-shopping journey using a fake EC2 control service and durable coordination outside the simulated host. This does not provision AWS or prove service eligibility.
- [ ] Validate each invitation's absolute testing window and revocation outside EC2 before wake. Plain page visits and invalid/expired/revoked invitations never start the host; restarting cannot renew access. Application admission revalidates access when startup finishes.
- [ ] Coalesce concurrent wake requests and enforce bounded requests/polling, retries and cooldown. Return promptly from startup requests; no long-running function waits for boot. Declare readiness only after application prerequisites pass and give a clear deadline/failure response.
- [ ] Shut down after 60 minutes of genuine inactivity with finite authenticated presence leases and a startup grace period. Ignore heartbeats, health probes and abandoned browser connections; accepted queued work, model requests and in-flight Actions prevent idle stop.
- [ ] Serialize admission, drain and stop through durable lifecycle authority. Recheck for new activity before committing shutdown; after commitment, route arrivals through startup instead of accepting work on the draining host. Verify race, crash and stale-lease recovery without replaying uncertain Actions.
- [ ] Keep invitation secrets out of URLs/logs, bound anonymous endpoint abuse and restrict eventual control permissions to the designated host. Failure of control storage denies automatic wake safely.
- [ ] Demonstrate manual start/prewarming and explain commerce reset after Storefront restart. Record which controls the manual fallback still requires, including automatic idle stop.
- [ ] Keep Lambda adoption conditional on 02 and the final cost review. Record actual AWS lifecycle and IAM verification for later cloud acceptance; local evidence cannot establish it.

## 08 — Verify combined public readiness under concurrent use

**What to build:** Several independent invited Shoppers can use the complete local proxy setup within measured limits, including predictable overload and budget-exhaustion behavior.

**Blocked by:** 07 — invitation-gated startup and idle shutdown (which includes 04 and 06).

- [ ] Exercise five simultaneous Shoppers as the initial target, plus bounded overload, with controlled provider latency, new identities, cart changes, SSE and queued requests. Cover supported desktop Chrome/Edge and Android Chrome; exclude iPhone/Safari from initial claims.
- [ ] Exercise idle shutdown, simultaneous wake and new activity during draining; invitation validity, allowance and uncertain-Action protection survive stop/start.
- [ ] Measure CPU/RAM, queue time and application latency at several bounded load levels; distinguish workstation measurements from future EC2 capacity qualification.
- [ ] Publish concrete safe local configuration values and a candidate-host test procedure; do not infer throughput from registry capacity or fake-provider latency.
- [ ] Verify no cross-Shopper leakage, duplicate mutations, unbounded queue/log growth or allowance bypass during overload, exhaustion and restart.
- [ ] Run the relevant complete regression/format/lint/build checks and preserve failure evidence and limitations without paid inference.

## 09 — Finalize the costed CAP-04 handoff

**What to build:** The owner receives one consistent architecture and acceptance package with tested local preparation, an eligible network design and an explicit path to CAP-05/06/07.

**Blocked by:** 02 — account/network feasibility; 08 — combined readiness (which includes 01 and 03–07).

- [ ] Reconcile the chosen topology against browser evidence, account access, all-in costing and the owner-provided-domain and credit-only/no-upgrade constraints; any unresolved feasibility prevents acceptance.
- [ ] Deliver the final diagram, service inventory, trust boundaries, IAM/secret handling, state lifetime, allowance policy and retention decisions.
- [ ] Include reproducible deployment, release/rollback/teardown and cloud acceptance checklists; separate local evidence from AWS and real-model checks still pending.
- [ ] Record owner review and keep separate authorization for paid qualification and resource creation. No implicit increase to the OpenRouter allowance.
- [ ] Leave the parent issue unchanged; report whether its acceptance evidence is ready for an explicit closure decision. CAP-05 model qualification and CAP-06 deployment remain separate work.

## Test boundaries and execution frontier

The primary seam is a real browser through the HTTPS proxy into the existing services.
The additional allowance seam is the Agent request path with a fake provider and
real persistent storage/process restarts. Lifecycle rehearsal uses the same browser
journey with fake EC2 control and durable coordination. Infrastructure eligibility
uses owner evidence and official sources, not fabricated test fixtures.

The owner confirmed the scope and decisions after review. Nine individual tickets
are published in the ignored local tracker. Ticket 01 resolves desktop browser layout feasibility under the domain amendment.
Current frontier: 02, 04 and 05. Ticket 03 resolved local production routing; 04 may
implement invited admission, and 05 can enforce the durable inference allowance.
Missing account evidence may pause 02 while independent local work proceeds.
The parent CAP-04 remains open and unchanged. Publication authorizes specified local
preparation, not account changes, provisioning or additional inference spending.
