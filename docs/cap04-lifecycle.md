# Invitation-gated startup and idle shutdown

This is the local Ticket 07 rehearsal. It does not provision EC2, Lambda, DNS,
IAM or a managed control store. Automatic cloud wake remains conditional on
Ticket 02's account eligibility and complete cost estimate.

## Authority and state

The waiting service remains outside the simulated shopping host. Its initialized
SQLite lifecycle file and invitation authority survive host stop/restart. The
local Agent reads the same external authority; this shared-filesystem transport
is deliberately rejected in production configuration. A remote AWS control-store
adapter, its authentication and resource-scoped IAM still require qualification.

Opening the waiting page or polling status never starts the host. Only a valid
invitation in a same-origin POST body requests startup. Wake validates the absolute
window and revocation without consuming or creating an application grant. The
Shopper enters the code again after startup; normal ownership, quotas and
invitation revalidation still apply. No code enters URLs, browser persistence or
model context. Both services disable access logs; waiting responses are no-store
with restrictive CSP and no-referrer policy.

Concurrent requests share one durable generation. Startup HTTP finishes before
boot; a separate controller reconciles idempotent commands for its single fixed
host. Readiness requires built Agent, Storefront, Panel and state prerequisites,
not only a running process. Health observation happens outside the database writer
lock, with generation revalidation afterward. Failed prerequisites remove ready
status and deny new work; surviving work leases can finish safely.

## Bounds and shutdown

| Control                                       | Local policy                                                    |
| --------------------------------------------- | --------------------------------------------------------------- |
| Genuine inactivity                            | 3,600 seconds                                                   |
| Startup deadline / minimum startup grace      | 300 / 120 seconds                                               |
| Browser status polling                        | Every 5 seconds, at most 60 attempts, 5-second HTTP timeout     |
| Drain/recheck                                 | Separate durable decision, at least 5 seconds before commitment |
| Work lease / renewal                          | 45 / 10 seconds                                                 |
| Maximum live work leases                      | 128                                                             |
| Anonymous HTTP / status / wake                | 240 / 120 / 10 per minute globally, durable counters            |
| Active waiting requests / body / read timeout | 8 / 1,024 bytes / 5 seconds                                     |
| Failed commands                               | At most 3 attempts, 10-second backoff                           |
| Stop completion / restart cooldown            | 120 / 60 seconds                                                |

Successful accepted shopping requests and explicit, authenticated interactions
advance meaningful activity. Visible trusted keyboard/pointer events are reported
at most once per 30 seconds; the Bridge sends only a context-bound activity signal,
never field values. A stationary page, health checks, Snapshot reconciliation,
status polling and SSE traffic do not advance activity. Interaction authority is
finite: it extends the inactivity deadline once, without a timer renewing it.

Accepted HTTP/model/queued work holds renewable work leases. A delivered Action
retains a work lease after its HTTP request finishes, until its existing Task
state resolves or expires. Human questions do not become immortal work. A crashed
worker loses its lease; expired worker authority is latched closed and never
silently reacquired. Generations fence both admission and lease renewal.

Drain and admission serialize through the same durable transaction. A request
winning before commitment cancels drain; a request after commitment receives 503
and must return to the waiting page. Authority is checked again after asynchronous
Storefront validation and before event/model delivery. The controller never
replays Actions. Failed stop is visible as failed, not falsely reported stopped;
after bounded failure the owner must inspect and stop the designated host. A new
generation requires observed stopped state and the cooldown.

## Local owner rehearsal

Use an existing built local release and the external configuration from
[release recovery](cap04-release-recovery.md). Keep the external invitation and
lifecycle files outside the simulated host's release/state directory. Initialize
the lifecycle explicitly; missing files must never create fresh authority:

```powershell
python -B -m deploy.lifecycle initialize --path C:/demo-control/lifecycle.sqlite
```

Add the returned identity and absolute path as `LIFECYCLE_DB_ID` and
`LIFECYCLE_DB_PATH` in the restricted local-rehearsal configuration. Point
`ADMISSION_DB_PATH` at the initialized outside-host invitation authority. Then:

```powershell
python -B -m deploy.lifecycle serve --release C:/demo/releases/local --config C:/demo/state/runtime.env --logs C:/demo/logs
```

Open `http://localhost:4200/`. The waiting service is loopback only. It owns only
the designated built release's services on 4000/4100/8000; it will not replace
unrelated processes occupying those ports. Ctrl+C closes its owned processes.
For owner manual startup/presentation prewarming, add `--prewarm`. It uses the
same lifecycle and automatic idle stop; it does not bypass Shopper admission.

A Storefront restart starts a fresh cart, fictional orders and commerce authority.
Agent-only restart invalidates Agent authority while the surviving Storefront
cart remains. Page refresh alone does not reset commerce. Check the cart before
retrying any request whose outcome was uncertain.

The lifecycle file is exclusively initialized and integrity/identity checked;
missing, corrupt, full or inaccessible coordination denies automatic wake/work.
Time moving backward fails closed. Clock synchronization and control-plane
outage/manual stop procedures remain part of actual cloud acceptance. The fake
control object survives coordinator reopens; killing the entire Windows launcher
or installing a real Linux control-plane service is not qualified by this proof.

## Verification boundaries

Final serial verification on 18 October 2026: **713 Python/browser tests passed
in 728.29s**, **199 TypeScript tests**, builds/type checks, lint and formatting.
Both independent reviews cleared after the reproduced failure/race fixes. Local
07 is resolved; 08 combined concurrency and 02 account/network feasibility remain
open. The two Python warnings are existing dependency deprecations exposed by the
waiting server's WebSocket auto-detection; no test failed.

Controller/HTTP regressions use real persistent files, concurrent callers, fake
time and a designated fake host. They cover invalid/revoked/expired invitations,
coalescing, readiness loss, deadlines, cooldown, bounded failure, stale leases,
slow health probes and admission/stop races. The browser rehearsal starts actual
built shopping processes from the waiting page, rechecks revoked admission,
performs a cart Mutation and verifies fresh commerce after stop/start without
renewing invitation quotas. Existing release recovery regressions retain the
lost-result, stale Confirmation and Undo checks. None of this establishes cloud
costs, AWS entitlement, IAM correctness or EC2 capacity.
