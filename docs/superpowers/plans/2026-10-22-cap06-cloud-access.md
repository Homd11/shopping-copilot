# CAP-06 cloud access implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:executing-plans inline,
> test-first, followed by a fresh independent review.

**Goal:** Prepare exact-resource runtime/OAC policies and sign browser POST bodies.

**Architecture:** Pure deterministic bindings-to-JSON renderer, no deploy command.
Shared waiting page adds a Web Crypto digest before sending its existing POST.

**Tech Stack:** Existing Python/pytest, browser JavaScript/Web Crypto, Playwright.

**Spec:** docs/superpowers/specs/2026-10-22-cap06-cloud-access.md.

## Global constraints

- Stockholm/aws only; no AWS call, credential lookup, resource creation or push.
- No anonymous Lambda URL, provider switch or additional paid service.
- Exact instance/table/namespace/function/distribution/object-prefix permissions.
- No raw codes/events/bodies in logs, URLs, local/session storage or artifacts.
- Existing scope/gates, budgets, local safety behavior and runtime selection remain.

## Review focus

- Identifier wildcard/path/ARN injection must fail before output (Task 1).
- IAM actions and resource conditions must match AWS's current contract (Task 1).
- Viewer Origin must survive while cookies/query/Host/Authorization do not (Task 1).
- Hash must cover exact transmitted UTF-8 JSON, including non-ASCII input (Task 2).
- Crypto failure must not send a wake request or leave a code in the input (Task 2).

## Task 1: access bundle

Files: deploy/cloud_access.py, eval/tests/test_cloud_access.py; research note by
the background researcher. Interface CloudAccessBindings and render_cloud_access
return documented JSON sections, no SDK dependency.

- [x] Write tests for unsafe identifiers, distinct names, deterministic output,
      exact policies/OAC/forwarding and no unsupported IAM actions.
- [x] Run them RED before adding the renderer.
- [x] Implement validated frozen bindings and deterministic least-scope bundle.
- [x] Run focused tests GREEN and check each AWS requirement against the note.

## Task 2: browser signing

Files: agent/lifecycle/waiting.html, eval/tests/test_waiting_signing.py.
Reuse the exact body string for hashing and fetch; no third-party dependency.

- [x] Intercept all browser requests at a synthetic HTTPS origin. Pin digest,
      body, code cleanup, no URL/storage leak and hash-failure no-fetch behavior.
- [x] Run RED with the current unsigned page.
- [x] Implement Web Crypto SHA-256 and header before fetch.
- [x] Run browser tests and existing waiting/lifecycle/startup checks GREEN.

## Task 3: evidence and review

Files: lifecycle/deployment guide, checkpoint/handoff, dated evidence JSON.

- [x] Run relevant tests with a fresh release build; repository lint/format,
      pip and whitespace checks. Inspect every output.
- [x] Fresh-context independent review; reproduce/fix findings with regressions.
- [x] Record measured results and limitations, update checkpoint and commit locally.

## Execution ledger

Ruling: continue inline under the owner's go/continue authorization and selected
topology. This prepares access files rather than pretending an unfinished Lambda
runtime is a deployable stack. No new owner decision or resource is introduced.
Startup/controller function split is a builder choice within the selected Lambda
service; final invocation counts/costs and actual resource inventory remain gated.

Pre-flight: Task 1 custom origin header forwarding and Task 2 POST digest share
the exact x-amz-content-sha256 name. Handler routing remains unchanged. Existing
isolated worktree reused; original checkout untouched. Native Windows execution
records briefs and RED/GREEN in this durable ledger rather than POSIX task scripts.

Builder check: fresh reviewer found nothing important left to clarify. Research
verified dual Lambda permissions, viewer body digest, transactional DynamoDB IAM
actions, exact distribution source and managed cache policy. Runtime policies
grant neither the initializer's Query nor standalone PutItem; they are not an
IAM proof of the shared-namespace application protocol.

Task 1 RED: cloud_access module missing. Task 2 RED: both exact-body digest cases
had no header, and hashing-failure test still sent POST. GREEN after renderer and
shared-page Web Crypto header:26checks passed. Added HTTPS/localhost browser
cases with nonce CSP, same fixed destination per environment:28checks passed.

Ruling: accept only single-label general-purpose S3 bucket names. This narrower
local contract avoids DNS/IP/reserved-name ambiguities; no actual bucket exists
or is chosen yet. CloudFront's custom header allowlist does not exclude its own
required protocol/signature headers. Existing handler bounds still need deployed
qualification; no claim of a three-header delivered event is made.

Task 1: complete. Task 2: complete. Task 3: complete. Fresh independent review
clear with28focused checks passed in3.78s. Final affected lifecycle/startup/
executor/access/browser checks plus a fresh release build:159passed, zero failures
or skips in68.92s. Release includes the access renderer and changed waiting page.
ESLint/Prettier, Ruff check/format219files, pip and whitespace pass. Record evidence
and commit locally only; no effective IAM/deployed OAC/cost qualification claimed.
