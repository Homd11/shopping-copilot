# CAP-04 cross-site browser proof implementation plan

> Execute inline with superpowers:executing-plans; review the final evidence using code-review.

**Goal:** Determine whether the current linked Shopper journey can work across unrelated trusted HTTPS sites with third-party cookies blocked.

**Architecture:** Disposable loopback TLS proxy in front of the existing services. Rewrite only public origin literals in served assets, then compare unchanged Strict cookies against an explicitly experimental partitioned Storefront cookie. Keep all production sources unchanged.

**Tech stack:** Existing Node HTTPS/HTTP, OpenSSL, Windows user certificate store, Python and Playwright. Existing scripted provider and temporary SQLite catalogue only.

**Spec:** CAP-04 cloud-readiness ticket 01 and docs/cap04-spec.md.

## Constraints and test seam

The approved seam is the actual browser through HTTPS into the existing services. Use unrelated registrable test domains, valid name-constrained certificates, default TLS verification and observed cookie-blocking controls. No public DNS, paid calls, AWS resources, secret output or weakened application authority. The owner explicitly approved temporary user-store certificate trust and removal. TLS keys and raw results stay in ignored scratch storage; reproducible evaluation-only probe source and sanitized evidence are tracked. This is a feasibility experiment, not production configuration adoption.

## Review focus

- A cookie setting flag without a blocking negative control is insufficient evidence.
- Embedded and top-level Storefront identities may occupy different cookie partitions.
- Concurrent browsers/tabs must preserve ownership and lease behavior.
- TLS bypasses or localhost-only sites cannot establish the requested browser result.
- Refresh/SSE reconnect must not duplicate accepted cart actions; Confirmation and Undo remain bound.

## Task 1: build and run the disposable browser experiment

- [x] Prepare isolated proxy and TLS material in `.scratch/cap04-cloud-readiness/probe/`; restrict the CA to the two test domains, trust only for this run, and remove its exact thumbprint in cleanup.
- [x] Build existing browser assets, start scripted services with exact test origins and temporary catalogue, route only allowed loopback hosts, and reject external browser requests.
- [x] Observe current Strict-cookie failure and SameSite=None unpartitioned failure with third-party blocking; then change only the experimental Storefront cookie to Secure/SameSite=None/Partitioned.
- [x] Verify linking, product open/add, two-browser cart isolation, refresh, two tabs, Confirmation/Undo and SSE reconnect where the candidate permits; record negative outcomes instead of broadening this ticket into runtime implementation.
- [x] Report actual browser versions and explicitly separate desktop results from untested Android hardware.

## Task 2: publish the verdict and check the work

- [x] Preserve a reproducible probe source reference and sanitized evidence; never commit keys, cookies or raw traffic.
- [x] Update ticket/checkpoint/handoff with exact completed and unverified criteria; do not close parent CAP-04.
- [x] Run relevant documentation formatting/diff checks and existing local regressions once; review standards and spec evidence independently, then commit the documentation.

## Execution ledger

- Initial source inspection: Storefront and Agent cookies are Strict; Panel/Bridge contain literal localhost origins. Production origin configuration is ticket 03. The probe therefore rewrites served public asset literals only and records this limitation.
- Ruling: no new product behavior or language interpreter changes; certificate trust is separately owner-approved and scoped to disposable test names.

- Observed: CDP-only Chromium 153 passed the scoped journey, but the equivalent Chrome 154 control allowed the unpartitioned cookie. Added actual profile preferences before treating desktop results as acceptance.
- Observed: Chrome 154 and Edge 155 with verified cookie blocking deny iframe sessionStorage. Partitioned cart HTTP succeeds, but Bridge initialization fails. This is the ticket's permitted negative result, not a fixed product or deployment qualification.
- Ruling: retain the minimal reproducible harness under eval/probes (evaluation-only, never imported by runtime); only generated keys, logs, catalogue and results are scratch artifacts. This supports review and reproduction without committing credential material.
- Ruling: do not broaden the probe into a recovery implementation. A memory-only substitute would weaken replay protection; the design must address journal authority before ticket 03.

- Review: standards found cleanup ordering could skip trust removal; independent cleanup plus two focused red/green failure tests fixes it. Spec found a reconnect overclaim; renamed it to connection restoration and explicitly left Action replay unverified. Both reviewers confirmed their findings resolved.

- Verification: 619 existing Python regressions, 182 TypeScript tests and two new cleanup tests passed; builds, format and lint passed. Chrome/Edge cross-site acceptance remains an explicit negative result.
