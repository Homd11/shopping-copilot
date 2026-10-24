# CAP-06 public HTTPS preparation implementation plan

> **For agentic workers:** Use superpowers:executing-plans to implement this bounded
> plan inline. This is local preparation, not cloud deployment or gate closure.

**Goal:** Package a separate public-ACME Caddy profile and prove its configuration
offline while preserving the existing static-certificate rehearsal profile.

**Architecture:** The approved direct ingress serves app.scpilot.tech and
store.scpilot.tech. Keep the current proxy routes, CSP, secret stripping and SSE
behavior; only the public profile enables automatic certificate management and
uses fixed public hosts/upstreams. The existing runtime does not launch Caddy and
will not automatically select this profile.

**Tech stack:** Existing Caddy 2.11.7, Python/pytest and immutable release builder.
No dependency installation or infrastructure tooling changes.

**Spec:** docs/superpowers/specs/2026-10-19-cap04-stockholm-ingress-amendment.md,
docs/cap04-deployment-handoff.md and docs/cap04-release-recovery.md.
Base: 45eb2d3. Owner continuation authorizes local preparation; preserve the
existing isolated checkout and implement inline under that authorization.

## Global constraints

- Keep Free plan, Stockholm and USD0 cash; no AWS calls, resource creation, DNS
  writes, certificate requests, provider switch or additional inference.
- CAP-05 remains open: two failed diagnostics, zero applied runtime quotas last
  verified 20 October, both allowance ledgers disabled. No fallback qualification.
- Keep the static evaluation Caddyfile unchanged and retain its loopback default.
- Public profile uses exactly app.scpilot.tech and store.scpilot.tech on HTTPS,
  Agent 127.0.0.1:8000 and Storefront 127.0.0.1:4000. No browser-selected upstream.
- Keep certificate/account state outside immutable releases on retained encrypted
  storage, restricted to the eventual service owner. No state in the artifact.
- Preserve off-origin, Sensitive Field, bound Confirmation, stale/duplicate Action
  and uncertain-outcome refresh protections; this slice changes no application code.

## Review focus

1. ACME provisioning must not occur during offline checks: use `caddy adapt`
   without `--validate`, never `run`, `start` or `reload` on the public profile.
2. Public host/upstream identity cannot depend on inherited rehearsal overrides.
3. Public routing must preserve private-route rejection, header stripping, CSP,
   no-store and streamed response settings; compare adapted route contracts.
4. Certificate storage must remain an external runtime input; no certificates,
   credentials or generated Caddy state may enter a release.
5. Adding the profile must not cause the runtime to launch it or make a modified
   artifact selectable; verify packaging and tamper refusal through release CLI.

## File structure

- Create deploy/Caddyfile.public: separate fixed-host public-ACME profile.
- Create eval/tests/test_public_https.py: offline real-Caddy adaptation checks.
- Modify deploy/artifact.py: include the new configuration in the file allowlist.
- Modify eval/tests/test_release.py: built-profile inclusion and tamper refusal.
- Modify deploy/README.md: profile selection, persistent state and offline limits.
- Update PROJECT_CHECKPOINT.md and handoff.md with measured results and next gate.

## Task 1: Separate public profile with preserved routing

**Interfaces:** Existing deploy/Caddyfile remains unchanged. New profile consumes
only COPILOT_PANEL_ROOT and COPILOT_CADDY_STORAGE; hosts, bind and upstreams are
fixed. Use the existing trusted Caddy executable through CADDY_BINARY, PATH or the
already-installed local probe tool. Tests explicitly skip if no executable is
available; the actual local run must use the pinned 2.11.7 binary.

- [x] Write adaptation tests: public TLS automation contains only the two approved
      subjects with an ACME issuer, no static certificate loader, admin disabled,
      persistent external storage, strict SNI/Host, normal automatic HTTPS and
      TCP HTTP/1.1+HTTP/2. Inherited test-host, bind, upstream or certificate values
      cannot alter the fixed public identity.
- [x] Test the public HTTP route tree equals the existing rehearsal route tree
      after normalizing only public hosts, public bind, file root and fixed Agent
      upstream. This preserves private path refusal, exact frame origins, no-store,
      secret stripping, route allowlists and SSE limits at the Caddy parser seam.
- [x] Run the tests and observe failure because the public configuration is absent.
- [x] Add deploy/Caddyfile.public. Use the approved public hosts, bind 0.0.0.0,
      existing route definitions and explicit Let's Encrypt ACME issuer. No shared
      route extraction or local-profile changes in this slice.
- [x] Run `python -m pytest eval/tests/test_public_https.py -q`; require real
      adaptation checks pass without provisioning or starting a public listener.

## Task 2: Include the profile in verified immutable releases

**Interfaces:** `deploy.artifact.build(source, output, local=False)` and existing
manifest verification remain unchanged; only the copied configuration inventory grows.

- [x] Extend built-release coverage: both Caddy profiles present with source-matching
      content and file hashes; no TLS state included. An installed release with a
      modified public profile must fail `python -m deploy verify`.
- [x] Run the focused release test and observe missing-profile failure.
- [x] Add deploy/Caddyfile.public to the existing artifact allowlist.
- [x] Run `python -m pytest eval/tests/test_release.py eval/tests/test_public_https.py -q`.
      Require all checks pass, including built-service restart/uncertain Action,
      invitation and allowance preservation. No real-provider calls.

## Task 3: Verification and durable handoff

- [x] Document the profile as prepared but not deployed. Explain trusted storage/
      root inputs, fixed hosts/upstreams, TCP80/443 and outbound issuer prerequisites,
      retained certificate state, stop-time renewal limitation and readiness checks.
- [x] Provide only an offline `caddy adapt` example for this stage. Explicitly state
      adaptation is weaker than module validation and proves no DNS, issuance,
      renewal or public browser behavior. Cloud use still needs its resource and
      account gates; do not label the local artifact production-ready.
- [x] Run Ruff check/format, relevant pinned Prettier checks, Caddy fmt diff and
      git diff whitespace check; release tests provide actual build evidence.
- [x] Obtain the fresh-context review required by executing-plans, address material
      findings with RED/GREEN where behavior changes, and preserve actual evidence.
- [x] Update checkpoint/handoff and commit only this slice locally. No push.

## Execution ledger

Ruling: implement this small configuration slice inline under the owner's explicit
continuation of local preparation, without another permission round. The topology
is already approved. Let's Encrypt as the single explicit ACME issuer and TCP
HTTP/1.1+HTTP/2 are implementation choices; actual issuer/network eligibility and
public TLS remain CAP-06/07 checks. A failed offline check never triggers issuance.

Deferred: remote DynamoDB authority/lifecycle implementation, AWS resource/IAM
templates and apply, DNS, Caddy service installation and host certificate readiness,
Bedrock qualification, and actual public browser/operational acceptance.

Execution: all tasks implemented and verified. Four expected missing-profile RED
failures preceded the profile/packaging change. One test expectation was corrected
to include Caddy-generated ACME challenges.bind_host=0.0.0.0; routes and security
assertions were not relaxed. Final combined suite14passed/no skips in148.60s;
fresh reviewer clear and independently3adapt checks passed. ESLint/Prettier/Ruff/
Caddy formatting/whitespace pass. Existing rehearsal profile byte-identical to
base; no public listener, module provisioning, issuance, AWS/model call or provider
switch. Evidence: eval/evidence/cap06-public-https-20261021.json. No full unrelated
browser/model suite rerun; this slice's real release builds and restart regression
suite are the relevant validation. Commit locally only; no push or gate closure.
