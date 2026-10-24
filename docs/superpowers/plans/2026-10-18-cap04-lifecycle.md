# CAP-04 invitation-gated lifecycle implementation

**Spec:** `docs/cap04-spec.md`, local ticket 07. **Base:** `476cb30`.
Execute inline under the owner's continuing `implement` authorization.

## Constraints and seams

Use existing invitation windows, ownership and Confirmation; no interpretation,
provider, AWS, DNS, paid calls or credentials changes. Idle threshold is 3,600
seconds. Coordination and invitation authority survive destruction of the
simulated host. Actual Lambda/storage/IAM selection remains conditional on 02.
Agreed seams: browser/service lifecycle, fake EC2 controls and real durable
coordination; existing Agent HTTP and browser recovery regressions.

## Review focus

- Concurrent starts and a controller crash must not multiply host commands.
- Revocation/expiry during boot must deny application admission.
- New work racing drain must either win admission or wait for another startup.
- Disconnected tabs/health/SSE must not renew meaningful activity.
- Missing/corrupt storage must not create fresh lifecycle or invitation state.

## Tasks

1. Add transactional lifecycle storage and controller at `agent/lifecycle/`.
   Red/green public controller tests in `agent/tests/test_lifecycle.py`: invalid
   invitations, coalesced starts, readiness, deadlines, durable reopen, idle drain,
   active work, stop commitment, stale leases and manual prewarming. Fixed finite
   limits, generation fencing and separate drain/commit ticks.
2. Add bounded waiting HTTP service and static page. POST body-only codes,
   same-origin checks, no access logging or browser persistence, bounded polling
   and terminal failures. Test through actual HTTP/browser seams with fake EC2.
3. Integrate optional local-rehearsal lifecycle authority into Agent admission,
   meaningful activity and active work leases. No deployment default changes.
   Test authenticated HTTP acceptance versus stop and retain restart protections.
4. Rehearse waiting-to-shopping against built processes, manual start, expiry,
   shutdown/restart and commerce reset. Document explicit local/cloud limits.
5. Run focused then full checks once, independent Standards/Spec review against
   base, resolve reproduced findings, update checkpoint/handoff/tracker and
   commit locally. No push implied.

## Execution ledger

- Plan initialized. Existing isolated worktree reused; original checkout untouched.
- Ruling: local coordination uses SQLite outside the simulated host; the same
  outside-host invitation authority is used by wake and application admission.
  This is a rehearsal adapter, not an AWS storage or topology selection. A real
  deployment must replace this transport under the later cloud gates.
- Implemented controller, bounded waiting HTTP/page, optional Agent work leases,
  trusted interaction reporting and fixed-host built-process rehearsal adapter.
- RED/GREEN: missing controller/HTTP/Agent integration; stale generation; slow
  observation blocking writer renewal; stale authorization after awaited ownership;
  unhealthy readiness; unbounded failed stop; false stopped observation; degraded
  readiness during request-to-Task lease handoff; pre-admission activity reporting.
- Review rulings: observations run outside the transaction and recheck generation;
  control commands are prompt/idempotent and serialize within it. Failed commands
  retain durable bounded attempts/backoff; failed shutdown never confirms stopped.
  Existing accepted tokens transfer to pending Task protection without new admission.
- Independent Standards review cleared; Spec review cleared after its additional
  degraded-lease and failed asynchronous stop findings were reproduced and fixed.
- Focused lifecycle/controller/browser run: **17 passed in 56.29s**. Built journey
  rejects revoked code, adds a cart product, stops/starts, observes empty commerce
  and preserves the existing redemption accounting. No paid calls or cloud changes.
- Final serial full regression: **713 passed in 728.29s**, exit code 0, durable
  ignored log/result JSON under `outputs/cap04-lifecycle-verification/`.
  TypeScript **199** tests, builds, types, ESLint, Ruff check/format and Prettier
  pass. Both independent reviews cleared. Staged sources scanned against actual
  configured secret values and key shapes, with no hits or forbidden paths.
- All five tasks complete. Local 07 resolved; next 08. Ticket 02 and parent CAP-04
  remain open. No deployed lifecycle/IAM evidence, paid calls or remote changes.
