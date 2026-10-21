# CAP-06 controller runtime implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL superpowers:executing-plans inline
> with TDD and one fresh final review.

**Goal:** Compose bounded startup/controller factories and authenticated observation.
**Architecture:** Inject SDK/HTTP transports into the existing durable protocol.
**Tech Stack:** Python, boto3/httpx, standard HMAC, pytest/Moto/Stubber.
**Spec:** docs/superpowers/specs/2026-10-22-cap06-controller-runtime.md.

## Global constraints

- No AWS/model call, resource creation, provider/factory activation or secret generation.
- Exact Stockholm host/function, zero SDK/application retry or claim takeover.
- Readiness requires fresh release/generation-bound proof, not liveness HTTP200.
- GET status/observe never starts EC2; uncertain outcomes retain durable state.
- No new service/scheduler, no body/code/credential logging; existing gates persist.

## Review focus

- Freshness/type/size failures in authenticated readiness (Task 1).
- Stale observation after I/O cannot change newer state (Task 2).
- Old/duplicate observer events cannot claim START or a newer generation (Task 2).
- Uncertain async enqueue must not refund/restart durable intent (Task 3).
- Wrong-role clients, unsafe SDK config or extra event fields refuse (Tasks 2–3).

## Task 1: authenticated fixed-host readiness

Create agent/lifecycle/readiness.py and agent/tests/test_readiness.py. Interfaces
readiness_reply and HTTPSReadinessProbe.check match spec; helper stays inactive.

- [x] Write/run RED for proof mismatch/replay, exact body bounds, TLS/URL settings,
      redirects, invalid request types and ordinary health rejection.
- [x] Implement HMAC reply/probe and run GREEN with MockTransport only.

## Task 2: trusted controller observation and filtered claims

Create agent/lifecycle/controller.py and agent/tests/test_control_worker.py;
modify durable claim/executor optional operation/generation filters.

- [x] Write/run RED for filtered claim, exact describe, stale revision/gen, bad
      observations and observe-only pending START refusal.
- [x] Implement ControlObserver/ControlWorker and prove duplicate dispatch/idle stop,
      cleanup safety and zero retries with Moto+Stubber.

## Task 3: injected runtime factories and notification

Create agent/lifecycle/lambda_runtime.py and agent/tests/test_lambda_runtime.py;
extend create_startup_handler optional notifier after safe accepted operations.

- [x] Write/run RED for role validation, lazy bounded SDK creation, exact async
      Event payload/target, no notification on denial and uncertain queue retention.
- [x] Implement validated settings and factories; keep environment/app selection
      and actual package/handler deployment disabled. Run GREEN.

## Task 4: verification and handoff

- [x] Add fresh release packaging assertions; run affected regressions, browser
      signing, repository lint/format, pip and whitespace checks.
- [x] Independent review; reproduce/fix material findings with regressions.
- [x] Record results/evidence, checkpoint/handoff, scheduling/host/package gaps;
      commit locally with no push or cloud acceptance claim.

## Execution ledger

Ruling: continue the owner-selected topology inline. HMAC is a builder choice to
avoid promoting ordinary liveness to readiness. No actual key or resource is
created. HTTP polling is not declared a reliable external scheduler; that gap is
an activation gate. Existing isolated worktree reused, original checkout untouched.
Pre-flight: claim filters feed worker; authenticated probe feeds revision-bound
observer; factories compose those interfaces and optional HTTP notification.
No incompatible signature changes; no environment-selected runtime activation.

Builder check: fresh reviewer found nothing important left. Task 1 RED: missing
readiness module. Streaming tests initially used preconsumed MockTransport replies;
confirmed that simulator state and made the harness yield actual byte streams.
20initial proof checks passed, then added malformed generation and MAC direction/
readiness-bit tests. No production fallback for consumed or unsigned replies.

Task 2 RED: missing controller module; separately reproduced legitimate EC2 high
state byte being marked uncertain by executor. Shared uint16/low-byte validation
now follows the AWS contract. Generation/operation filters are applied inside the
durable claim snapshot. Reproduced client policy changing during observation-token
I/O with a direct observer test, then added the final pre-describe policy check.

Task 3 RED: missing runtime module. Role-specific factories/notifier tests14passed,
then full intercepted wake/queue/start/signed-readiness flow, lazy SDK options and
malformed acceptance tests passed. Startup constructs no EC2 client; controller
constructs no Lambda client. Unknown queue ack retains the same wake generation.

Independent review found raw HTTPX rechunking delayed the body deadline under a
slow stream. RED regression consumed1025one-byte chunks/simulated seconds. Changed
to raw chunks with per-chunk deadline checks; reviewer reproduction now stops at
two chunks/two simulated seconds. Review clear with93focused checks independently
passed in23.09s. Bounded per-phase HTTP timeouts are not an atomic wall-clock
deadline; the monotonic body guard prevents prolonged drip buffering.

Ruling: default SDK's ordinary role credential chain remains available only when
the explicit future runtime factory is called. Application bindings are never
read from process environment; no import-time client or active handler is added.
Fixed endpoint/TLS/proxy/retry options are intercepted and asserted locally.

Tasks 1–4: complete. Final focused independent review clear after streaming fix:
93passed23.09s. Final broad admission/lifecycle/allowance/control/access/browser
tests plus fresh self-contained release build:308passed, zero failures/skips94.71s.
ESLint/Prettier, Ruff check/format225files, pip and whitespace pass. New modules
are packaged in the general release; an actual Linux Lambda dependency/bootstrap
package and host activation remain explicitly pending. Commit locally only.
