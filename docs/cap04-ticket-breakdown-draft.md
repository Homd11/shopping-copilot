# CAP-04 cloud readiness: proposed tickets

**Status:** Draft for owner approval; not yet published to the local tracker.

Source: approved 11 October cloud-readiness design and the accompanying spec draft.
The parent CAP-04 ticket remains unchanged. Numbers are local to this feature.
Independent tickets may start at the frontier; this does not authorize parallel
agents or any external actions. Account facts and provisioning permissions are
separate from ticket-to-ticket blockers.

## 01 — Prove cross-site Shopper identity through HTTPS

**What to build:** A disposable browser/proxy rehearsal that shows whether a Shopper can use the embedded Storefront across unrelated HTTPS sites while third-party cookies are blocked.

**Blocked by:** None — can start immediately after publication.

- [ ] Reuse the current linked Shopper journey with a scripted provider, valid HTTPS and genuine cross-site hostnames; report browser versions and privacy settings.
- [ ] Demonstrate two-browser cart isolation, linking, refresh, two tabs, opening a product, add, Confirmation/Undo and SSE reconnection without repeated Actions.
- [ ] Investigate partitioned embedded authority without disabling privacy, CSRF, ownership or source-window validation; distinguish embedded and top-level storage behavior.
- [ ] Record a supported configuration or an explicit negative result. Keep probe changes disposable; do not silently adopt an unsuccessful topology.

## 02 — Establish account and complete network-cost feasibility

**What to build:** A reviewable choice of eligible ingress, egress and hosting that can provide the public demo within available credits without upgrading the AWS account.

**Blocked by:** None — can investigate alongside 01.

- [ ] Reconcile owner-provided current plan, credits, expiry, service/model access and regional evidence; never fabricate entitlement or use first inference as a read-only access test.
- [ ] Compare the candidate private origin with the documented alternatives, including model access, deployment artifacts, administration and maintenance egress.
- [ ] Produce the complete two-month bill of materials, traffic/token assumptions, qualification allocation and contingency; distinguish reference estimates from a quote.
- [ ] Explicitly exclude unavailable flat-rate plans and automatic paid upgrades. Mark unavailable account evidence as an external blocker, not a passing gate.
- [ ] Make no resources, purchases, subscription acceptances or model calls. A feasible network choice remains conditional on the browser result from 01 and is reconciled in 08.

## 03 — Run a Shopper journey through production origin configuration

**What to build:** The existing shopping journey works locally through the production-style HTTPS proxy with configurable public origins and private service routing.

**Blocked by:** 01 — successful browser feasibility result.

- [ ] Carry the successful browser configuration into the actual services; serve built assets without development reloaders and keep application ports on loopback.
- [ ] Preserve exact public origin and iframe source checks, authenticated private reads, CSRF, cookies and current Action safety across browse, add and guarded confirmation.
- [ ] Show isolation with two browser contexts; malformed origin/host configuration fails clearly and no browser input selects an arbitrary private destination.
- [ ] Demonstrate SSE initial delivery, heartbeat, cursor reconnect and Stop through the proxy; personal responses and Set-Cookie never cross cache/user boundaries.
- [ ] Public mode excludes test/reset endpoints. This local runtime configuration does not claim CloudFront or AWS deployment qualification.

## 04 — Admit invited Shoppers with bounded public usage

**What to build:** An invited Shopper can enter and use the demo while expired, revoked or excess access receives a clear response before model work.

**Blocked by:** 03 — production origin journey.

- [ ] Record finite invitation lifetime, redemption and revocation rules; exchange secrets without URLs/logging, and preserve existing Shopper ownership after admission.
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

## 07 — Verify combined public readiness under concurrent use

**What to build:** Several independent invited Shoppers can use the complete local proxy setup within measured limits, including predictable overload and budget-exhaustion behavior.

**Blocked by:** 04 — admission; 06 — release/recovery (which includes 05).

- [ ] Exercise representative concurrent browser sessions with controlled provider latency, including new identities, cart changes, long SSE connections and queued requests.
- [ ] Measure CPU/RAM, queue time and application latency at several bounded load levels; distinguish workstation measurements from future EC2 capacity qualification.
- [ ] Publish concrete safe local configuration values and a candidate-host test procedure; do not infer throughput from registry capacity or fake-provider latency.
- [ ] Verify no cross-Shopper leakage, duplicate mutations, unbounded queue/log growth or allowance bypass during overload, exhaustion and restart.
- [ ] Run the relevant complete regression/format/lint/build checks and preserve failure evidence and limitations without paid inference.

## 08 — Finalize the costed CAP-04 handoff

**What to build:** The owner receives one consistent architecture and acceptance package with tested local preparation, an eligible network design and an explicit path to CAP-05/06/07.

**Blocked by:** 02 — account/network feasibility; 07 — combined readiness (which includes 01 and 03–06).

- [ ] Reconcile the chosen topology against browser evidence, account access, all-in costing and the no-domain/no-upgrade constraints; any unresolved feasibility prevents acceptance.
- [ ] Deliver the final diagram, service inventory, trust boundaries, IAM/secret handling, state lifetime, allowance policy and retention decisions.
- [ ] Include reproducible deployment, release/rollback/teardown and cloud acceptance checklists; separate local evidence from AWS and real-model checks still pending.
- [ ] Record owner review and keep separate authorization for paid qualification and resource creation. No implicit increase to the OpenRouter allowance.
- [ ] Leave the parent issue unchanged; report whether its acceptance evidence is ready for an explicit closure decision. CAP-05 model qualification and CAP-06 deployment remain separate work.

## Proposed test boundaries and review

The main seam is a real browser through the HTTPS proxy into the existing services.
The additional allowance seam is the Agent request path with a fake provider and
real persistent storage/process restarts. Infrastructure eligibility uses owner
evidence and official sources, not fabricated test fixtures.

Approve or adjust ticket sizes, blocking edges and these test boundaries before
publishing one ready-for-agent file per ticket. Initial frontier: 01, 02 and 05;
01 is the recommended first task because it can invalidate the proposed ingress.
Missing account evidence may pause 02 while the independent local work proceeds.
