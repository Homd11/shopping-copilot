# CAP-04 production origin journey implementation plan

> **For agentic workers:** use superpowers:executing-plans inline, task by task.

**Goal:** run the existing shopping journey through configured sibling HTTPS origins and a maintained proxy without evaluation asset rewriting.

**Architecture:** Panel builds contain validated public origins; Storefront HTML supplies the validated Panel origin to Bridge. Caddy terminates local TLS, serves the built Panel and routes fixed loopback services. Agent emits SSE keepalive comments. Evaluation controls run outside the public proxy.

**Tech stack:** existing TypeScript/Vite/Express/FastAPI; Caddy 2.11.7 for the rehearsal.

**Spec:** docs/cap04-spec.md, ticket 03 and docs/cap04-domain-https-plan.md.

## Global constraints

- Public names: https://app.scpilot.tech and https://store.scpilot.tech; local rehearsal uses sibling .test names.
- No DNS writes, AWS resources, account upgrades or paid calls.
- Exact origin/source, host-only Strict cookies, CSRF, Confirmation, Sensitive Field exclusion and uncertain-outcome recovery remain required.
- Existing journal stays in Storefront sessionStorage; no prompt changes.
- Public mode disables evaluation routes even if evaluation environment flags are present.

## Review focus

- A malformed or mismatched origin must stop linking before an Action executes.
- Forged Host or internal-route requests must never reach a privileged handler.
- Cache reuse must not share cookies, personal HTML or carts.
- Reconnected SSE must carry a native cursor and not replay a completed Mutation.
- Stop and idle SSE must work without weakening ownership or extending shopper activity through heartbeats.

## Task 1: configured browser origins

Files: bridge/src/public-origins.ts, panel/vite.config.ts, panel/src/main.ts,
store/src/shopper-http.ts, store/src/app.ts, bridge/src/runtime.ts.
Public contract: validatePublicOrigin(raw, production): string. Panel build defines
only the public Agent/Storefront/Panel origins. Storefront emits a
copilot-panel-origin meta value; Bridge validates it and exact current Storefront
origin before accepting parent messages. Defaults stay local-development only.

- [x] Write and run a failing public-origin validator test:
      `expect(() => validatePublicOrigin("https://app.scpilot.tech/path", true)).toThrow()`.
- [x] Implement exact canonical-origin validation, HTTPS in production, loopback-only HTTP otherwise, and no credentials/path/query/fragment.
- [x] Test Storefront HTTP output contains configured Panel metadata and never service secret; verify unsafe metadata cannot inject HTML.
- [x] Integrate validated Vite public definitions and Bridge metadata bootstrap; run focused tests and typechecks.

## Task 2: production service boundary and SSE

Files: store/src/identity-config.ts, agent/app.py, agent/session_stream.py,
agent/tests/test_public_runtime.py, store/tests/public-runtime.test.ts.

- [x] Write failing service tests for production + evaluation flag: test/reset/step routes remain unavailable.
- [x] Enforce production evaluation exclusion in both services and explicit production secret configuration.
- [x] Add a comment keepalive to the existing authorized SSE polling loop every 10 seconds, including initial connection; no event ID or activity touch.
- [x] Test heartbeat output at the HTTP/SSE seam with the scripted provider; rerun existing ownership/recovery checks.

## Task 3: Caddy route configuration and browser rehearsal

Files: deploy/Caddyfile, deploy/README.md, eval/probes/cap04_cross_site.py,
eval/probes/cap04_runtime_control.mjs.

- [x] Validate a Caddy configuration with explicit public hosts, provided TLS files,
      built Panel root, fixed loopback upstreams, no caching of private responses,
      streamed SSE and internal/test-route rejection. Unknown hosts get no application route.
- [x] Add runtime mode to the probe; build Panel under configured origins, start
      services in production, use Caddy instead of asset rewriting. Control iframe and
      forced stream interruption use isolated evaluation servers outside the public proxy.
- [x] Run installed Chrome and Edge under verified third-party blocking: browse/add,
      isolated carts, refresh, tabs, Confirmation/Undo, SSE cursor/replay, Stop,
      public test/internal-route rejection, malformed Host and cache checks.
- [x] Verify exact CA/private-key cleanup and record Caddy version/checksum.

## Task 4: final verification and handoff

- [x] Run full relevant Python/TypeScript suites once, builds/typechecks and format/lint.
- [x] Obtain independent Spec and Standards reviews; fix material findings with focused regressions.
- [x] Record ticket evidence, current frontier and remaining AWS/Android gates; stage only intended files after credential checks; commit locally.

## Execution record

Base: f57fc30. Owner instruction: proceed with ticket 03; implement inline in the
existing CAP-04 worktree. The named browser/service boundaries were approved in
the ticket. Domain layout is approved; AWS network selection is still ticket 02.

Tasks 1–4 completed. Verification: 627 Python / 198 TypeScript tests, both installed
browser runtime journeys, builds/typechecks and lint/format passed. Review fixes:
escaped-host regression RED→GREEN; unchanged revocation tests RED→GREEN via
idle-only comment ordering; heartbeat evidence moved to browser downstream of
Caddy and passed both browsers. No scope ruling or deferred minor remains.
One-shot streams retain their existing payload; pending events precede idle comments.
