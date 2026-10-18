# CAP-04 combined concurrency rehearsal

**Spec:** `docs/cap04-spec.md`, local Ticket 08. **Base:** `da59a56`.
Execution is inline under the continuing `implement` authorization.

## Constraints and seams

No prompt, phrase interpretation, provider limit, AWS/DNS or OS trust changes.
Use the existing Caddy routing, actual Storefront/Agent/Panel, external admission
and allowance files, and an explicitly injected deterministic delayed provider.
The approved browser/HTTP, allowance and lifecycle seams remain the test boundary.
The installed Chrome/Edge and mobile-emulated journeys are workstation evidence;
physical Android and candidate EC2 capacity cannot be inferred from them.

## Review focus

- Five independent cookies/contexts must never share carts, sessions or SSE.
- An eight-request burst must refuse excess work within finite bounds.
- Queue delay, fake-model delay and browser latency must be measured separately.
- Expiry/exhaustion/restart must retain spent allowance and uncertainty.
- Sampling/reporting must exclude credentials and impose finite output bounds.

## Tasks

1. Add a reusable network-free capacity application under `eval/capacity/`, with
   controlled latency, fixed structured model decisions and content-free timing
   records. Test red/green at real Agent HTTP and inference entry seams.
2. Add a reproducible loopback HTTPS/Caddy browser runner for load levels 1/5/8,
   installed Chrome/Edge and Android emulation. Use a disposable certificate pinned
   only inside the temporary browser launch; never install a CA or disable TLS
   verification globally. Exercise actual cart mutations, cross-session denials,
   SSE reconnect/duplicates, overload and durable exhaustion. Collect bounded CPU,
   RSS, queue and elapsed measurements; use standard-library process sampling.
3. Compose existing lifecycle/restart cases and add any missing combined proof at
   their public seams. Leave physical Android and any unproved acceptance open.
4. Run focused checks, inspect measured results, independent Spec/Standards review,
   then relevant full repository verification. Record safe local limits and exact
   candidate-host procedure; commit locally without implying cloud qualification.

## Execution ledger

- Owner smoke-tested the live advisor successfully and authorized the next step.
- Reused existing isolated worktree, branch `codex/cap04-capacity`.
- Real API use is not part of load verification. Existing live session will be
  stopped through its recorded owned processes when fixed test ports are needed;
  its key, $2 cap and existing ignored configuration remain unchanged.
- Added explicit network-free delayed decision fixture, native owned-process
  sampling and real HTTPS/Caddy cohorts. The only production seam addition is an
  optional content-free queue observer whose failure cannot change authority.
- Failed harness runs retained: incomplete offline packaging environment, missing
  fixture target, expiring Undo equality, wrong feedback selector. Repaired the
  harness rather than weakening runtime guards. Overload release now waits for
  visible refusals instead of an arbitrary timer.
- Final Chrome002, Edge002 and mobile001 runs pass 1/5/8 cohorts, five accepted
  requests plus three refusals at overload, isolation, refresh and durable shared
  allowance exhaustion/disable. No paid calls. Measurements and limitations are
  published in docs/cap04-capacity.md.
- Combined Agent HTTP/lifecycle proof covers accepted/queued requests and pending
  Actions, drain arbitration, retained quotas/uncertainty and old-worker fencing;
  actual process-restart browser proof remains in the earlier regressions.
- Both independent reviews cleared implementation. Standards requested removing
  raw conversation/question diagnostics; replaced them with state/counts only.
  Follow-up reviews cleared the runbook and optional native Caddy path.
- Focused 28 checks pass in 12.49s; final serial full suite 716 pass in 733.52s,
  exit 0. TypeScript199/build/types/ESLint and Ruff check/format pass. Two upstream
  WebSocket deprecation warnings remain. Full evidence is ignored under
  outputs/cap04-capacity-verification/.
- Owner has a connected CMF Phone 1 and enabled USB debugging. Chrome discovery
  awaits phone authentication. Physical Android remains pending; keep Ticket08
  open. No trust store, DNS, AWS or paid inference changes. No push authorized.
- Superseding hardware result: owner accepted Google's SDK licence; Google-signed
  portable ADB reached authorized CMF Phone1 and Chrome155.0.8059.41. Actual phone
  plus four desktop contexts pass five isolated mutations, foreign404 both ways,
  refresh/no duplicate POST. Additional phone request refused with unchanged cart
  during held overload; eight desktop requests complete5/refuse3. Total fixture
  calls10, paid0. Evidence under outputs/cap04-capacity-android-001/.
- Owner handled disposable leaf warnings for USB-only sibling localhost HTTPS;
  no phone CA, public DNS or production source changes. One-off scripts remain
  ignored local experiment records; runbook includes repeat protocol and limits.
  Owned processes, test tab, forwarding, ADB server and key cleaned up/verified;
  owner instructed to turn USB debugging off. Local08 may close;02/09/parent and
  actual public-domain/EC2 acceptance remain separate gates. No additional full
  code-suite rerun is needed for evidence-only changes after the716/TS199 pass.

- Final independent Spec and Standards reviews inspected the hardware scripts and
  aggregate evidence; both clear documentation and bounded local08 closure.
