# CAP-06 Offline Provisioning Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prepare the retained AL2023 host's runtimes and swap with safe timer recovery, leaving the application disabled and the host stopped.

**Architecture:** A narrow operator procedure repairs the existing detached root before its next boot, then installs an immutable offline input bundle during a bounded private session. Separate gates cover local preparation, recovery resources and host writes; none is granted by this plan. No new orchestration framework or background worker is needed.

**Tech Stack:** AL2023.12.20261021 x86_64, systemd 252, XFS, native Amazon RPM/DNF, Python 3.12.14, Node.js 24.22.1, Caddy 2.11.7, nftables 1.0.4, existing 28-wheel lock.

**Spec:** [Offline provisioning design](../specs/2026-10-25-cap06-offline-provisioning-design.md). Read it alongside this procedure, including its exact input hashes and acceptance limits.

**Status, 26 October:** owner-approved design; local preparation below has executed.
See [its evidence](../../cap06-offline-provisioning-preparation.md). Tasks 2–5 remain
unexecuted pending the exact new resource/cost approval and their checks. No AWS
host boot, package install, real swap file or timer repair has occurred. Synthetic
files created during rehearsal were removed with their private test filesystems.

## Global constraints

- Reuse the recorded original Stockholm host and encrypted 20-GiB retained root; do not boot it before offline timer recovery.
- Preserve `/usr/bin/python3` / system Python 3.9.25, existing RPMs and root filesystem UUIDs.
- Application units stay disabled/inactive; no provider key, ledger, allowance, catalogue or invitation-state initialization.
- Free plan and USD0 cash remain mandatory; completed inspection approval does not authorize this next operation.
- Original root must never be deleted, formatted, repartitioned, force-detached or attached as a helper's boot root.
- Use 1-GiB swap, swappiness 10, unchanged service limits/concurrency, at least 4-GiB final free space and 1-GiB installation headroom.
- Fixed inputs only; no network fallback, package upgrades, global pip, container build or public activation.
- Retain startup-only model qualification validation and current OpenRouter USD2 accounting/holds unchanged.

## Review focus

1. Wrong or ambiguous secondary disk: refuse before writes; match exact volume identity and partition layout.
2. Missed persistent timer or unexpected drop-in: refuse boot until the old units are masked and only the new relative guard is enabled.
3. Incomplete RPM closure or scriptlet activation: refuse installation; preserve Python 3.9 and keep vendor nftables inert.
4. Linked/conflicting destination or partially written install: refuse replacement; preserve a bounded recovery record.
5. Low disk/RAM or active swap rollback: stop safely; never delete active swap, widen spending or claim capacity from a successful install.

## Files and records

No product code changes are required by this procedure. The future operator keeps
private records in a new ignored `.scratch/cap06-offline-provisioning/<operation>/`
directory with owner-only permissions. Exact account/resource/IP/key identities
stay there. A sanitized result may later be added under `eval/evidence/` and linked
from `PROJECT_CHECKPOINT.md` and `handoff.md`; no acceptance flag changes implicitly.

Create these records during the applicable future stages:

| Record                                               | Responsibility                                                                                                                                   |
| ---------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| `recovery-manifest.json`                             | Original/helper identities, AZ, root mapping/retention, discovered device/UUID, exact old/new timer bytes, backups and attachment reconciliation |
| `inputs.json`                                        | Exact artifact paths, bytes, SHA256, provenance/signature receipts, fixed metadata and complete additive RPM transaction                         |
| `rpm-before.txt`, `rpm-after.txt`, `dnf-preview.txt` | Installed NEVRA/providers, scriptlet review, no unexpected package replacement                                                                   |
| `host-before.json`, `host-after.json`                | Timer state, system Python identity, runtime versions, ownership, inactive services, swap and disk observations                                  |
| `teardown.json`                                      | Original stopped, original encrypted root retained/attached, temporary IP absent, helper-only disposal and any incomplete reconciliation         |

These are evidence records, not executable approval tokens. Fixed operation
identities and approved external deadlines must be reconciled separately before
any action. Do not run a manifest merely because it contains `approved=true`.

## Task 1: Close inputs and rehearse the two filesystem changes

**Consumes:** retained inspection receipt, the design's input pins, runtime/wheel locks and historical vendor records.
**Produces:** checked local artifacts and a list of remaining inventory-dependent RPMs; synthetic timer/swap rehearsal receipts. No cloud or original-root changes.

- [x] Owner approval on26October authorized local public documentation/signature acquisition and the bounded disposable Linux rehearsal. The earlier design-only offline boundary ended at that review; it did not authorize AWS operations.
- [x] Verify exact XFS read-only/writable mount behavior with duplicate UUIDs, compatible systemd offline unit handling and AWS stopped-root attachment requirements against primary documentation. Retain the exact tool versions and sources; do not treat candidate mount options in the spec as already tested.
- [x] Rehearse the timer procedure on a synthetic root with regular old unit files, an enable symlink and a synthetic expired stamp. Assert that only the two old units/their exact link/stamp are archived/masked, unrelated timers survive, and only the replacement `OnBootSec=90min`, `Persistent=false` timer is enabled. Repeat with wrong ownership, unexpected drop-ins and a linked backup path: expect refusal without partial replacement. No real poweroff command may run during this rehearsal.
- [x] Rehearse exclusive non-sparse 1-GiB swap-file creation on disposable XFS, exact mode/blocks, marked fstab/sysctl candidate files and exclusive-create refusal. The later configuration rehearsal also verified exact no-write repeats and seven foreign/link/conflict refusals. Activate only disposable swap if that rehearsal is explicitly permitted; never use the Windows/WSL host's own swap as a test target.
- [x] Recheck local retained hashes against the spec, `deploy/linux-runtime.json` and `deploy/requirements-linux.lock`. Retain the Node signature result; obtain/verify the missing Caddy publisher-signature material and trusted Amazon RPM signatures in the later authorized acquisition stage. Do not execute unverified binaries.
- [x] Leave the final RPM transaction pending until the complete original-root RPM/provider inventory is available. Native Python seeds are the three RPMs in the spec; Node/Caddy remain direct pinned binaries. Do not package all 19/14 extracted diagnostic RPMs as an install list.

**Result:** exact native systemd252 offline edits, seven unsafe-file refusals,
duplicate-UUID mounted-XFS recovery, clean-log diagnostics and a fully allocated
1-GiB XFS swap signature passed. Caddy/RPM signatures passed. Managed config repeat/no-write and seven refusal checks also passed. Host swap
activation, reboot persistence and complete actual RPM closure remain unverified
and are not claimed by these checked preparation items. No real host or
acceptance flag changed.

## Task 2: Prepare the next exact AWS operation proposal

**Consumes:** reviewed design/rehearsal and current retained custody.
**Produces:** owner-reviewable resource/cost/rollback proposal; no creation until its approval.

- [x] Prepare the exact public-price worksheet in `docs/cap06-private-provisioning-proposal.md`: USD0.14078071 estimate, USD0.16893685 with20%buffer, proposed USD0.25 incremental eligible-credit allocation. Actual account/credit coverage still requires the separately approved preflight; the earlier USD4.50 grant is not reused.
- [x] Bound the proposal (not an executed operation) to one same-AZ instance with its own encrypted root, no IAM profile/auto public IP, existing revalidated key/SSH-only SG if compatible, and one EIP reused sequentially between helper and original. State exact total running/allocation deadlines and API cleanup authority; helper and original guest guards are 90 minutes and do not extend those limits. No concurrent extra EIP, NAT, snapshot, DNS or application ingress.
- [ ] Explicitly approve only helper-instance termination and deletion of its exact temporary root after backup retrieval. Protect the original host/root/ENI/SG/key; ambiguity means stop/release and retain, never delete by name. Specify cleanup if root detach/attach or final verification fails.
- [ ] Establish original/helper stop permissions and external stop/IP-release fallback before launch. Confirm root encryption/retention/AZ ownership afresh during the authorized stage. Sign-in or Paid-plan requests must not silently widen scope.

**Exit check:** human approval applies to exact future quantities, credit ceiling, time window, writes and helper-only disposal. Until then, keep everything offline.

## Task 3: Repair the root offline and finish the RPM inventory

**Consumes:** Task 2's explicit approval, compatible rescue tooling and the design's recovery sequence.
**Produces:** reattached original root with replacement timer; frozen host-specific input closure; private recovery record.

- [ ] Launch/verify the bounded helper, establish SSH host trust and reconcile the original stopped root identity before detach. Attach the original as secondary and identify it by AWS-volume-to-Nitro mapping, partition and OS contents. Wrong/ambiguous device fails before writes.
- [ ] Mount/read first using the rehearsed XFS procedure. Capture UUID/PARTUUID and prove the helper root is excluded. Discover the canonical RPM database inside the original root, copy it to a protected helper workspace and query the copy with compatible RPM tooling; capture complete NEVRA and providers without executing target binaries or writing its database.
- [ ] Resolve a minimal additive closure from that inventory and fixed repository metadata. If reliable inventory/closure cannot be completed here, perform only timer recovery; the next approved original boot is inventory-only, followed by stop/review before any package install.
- [ ] Preview every package and scriptlet. Refuse erasure, downgrade, library/system-Python/kernel replacement or unapproved dependency. Freeze exact missing RPMs, byte lengths, hashes, signatures and approved transaction into `inputs.json` before installing; any later mismatch stops the operation.
- [ ] Save exact timer files/metadata/link/stamp, then perform the design's clean writable-root repair: old regular files moved aside, exact enable link removed, old timer/service names masked, exact old stamp archived if present, new relative timer/service written root `0644`, new timer enabled. Keep backup directory root `0700`. No global timer cleanup or helper `--now` action.
- [ ] Verify final guest paths/links and unit syntax; copy the small recovery backup to owner-held storage. Cleanly unmount, detach only after the filesystem is no longer mounted, and reattach the original root at its recorded original mapping with retention preserved. Reconcile API state before permitting original boot.
- [ ] Stop the helper, move/release the sole temporary IP under the approved sequence and complete approved helper-only disposal after backup retrieval and original-root detachment are confirmed. Record partial outcomes rather than retrying ambiguous detach/delete operations.

**Exit check:** root attached to its original stopped instance; old timer masked/new guard enabled; immutable package inputs ready or installation explicitly blocked. Original volume identity/UUID unchanged. Stop and release the IP if this task exhausts the approved window.

## Task 4: Install runtimes from the fixed offline bundle

**Consumes:** approved original-host writes, successful Task 3, frozen input manifest/closure and sufficient remaining time.
**Produces:** native runtimes and final-path venv, application still inactive.

- [ ] Verify at most 128-MiB bundle size, exact manifest/archive/wheel hashes, safe archive members and licenses before transfer/extraction. Use root-only staging, no traversal/escaping links or extracted ownership overrides. Existing native release must match the spec; any source change needs a new artifact review.
- [ ] Boot only with the approved external deadline and verified root repair. Immediately verify old timer/service masked and the new timer active/enabled with a future trigger, no calendar catch-up/drop-ins. Otherwise stop by API; do not try a second racing boot.
- [ ] Record system Python path/target/RPM/version, complete RPM inventory, free disk, swap and inactive application/vendor units. Recheck against the frozen inventory. Require at least 1-GiB staging headroom beyond planned final consumption and 4-GiB final free space.
- [ ] Persistently mask the verified vendor `nftables.service` before its RPM scriptlet runs; refuse unexpected existing unit/configuration. Preview the exact local RPM arguments with the following constraints, then inspect the result before the approved transaction. `EXACT_RPM_PATHS` below means an explicit validated argument list from `inputs.json`, never a wildcard or evaluated shell string.

```text
dnf --disablerepo='*' --releasever=2023.12.20261021 \
  --setopt=install_weak_deps=False --setopt=localpkg_gpgcheck=True \
  --assumeno install EXACT_RPM_PATHS
```

- [ ] Apply that same checked transaction with the preview-only flag removed. Reconcile installed NEVRA, scriptlet result, vendor unit still masked/inactive and unchanged system Python. On any partial failure, record/stop; do not automatically uninstall or retry with skipped dependencies.
- [ ] Install pinned Node/Caddy executable/license pairs into the spec's root-owned version directories; check complete bytes/modes before publishing the two `/usr/bin` bindings. Refuse foreign/RPM-owned destinations and unsafe ancestors. Keep Caddy without file capabilities.
- [ ] Create the venv **at its final path** using native `/usr/bin/python3.12`, then install only the locked 28 application wheels. The following are future commands after all path/ownership/input checks, not commands to run now:

```sh
/usr/bin/python3.12 -m venv --copies /opt/shopping-copilot/python
/opt/shopping-copilot/python/bin/python -I -m pip --isolated install \
  --no-index --find-links=/root/scpilot-provisioning/wheels \
  --require-hashes --no-deps --only-binary=:all: --no-compile \
  --disable-pip-version-check \
  -r /root/scpilot-provisioning/requirements-linux.lock
```

Run this with a sanitized environment and pip configuration disabled at all
scopes (verify the retained pip version's behavior first); `--isolated` alone
does not establish that system configuration was ignored. Assert the install
target is this venv and no index/version check is attempted.

- [ ] Check exact Python/Node/Caddy/nft versions and executable hashes, `pip check`, wheel inventory and native imports (SSL, SQLite, uvloop, httptools, pydantic_core, YAML). Native ensurepip tooling is separate from the 28 application distributions. No app lifespan, SDK/client construction, HTTP readiness, ACME or model call.
- [ ] Stage only root-owned release/code, no-login accounts, empty state/log directories and disabled prepared units according to `docs/cap06-host-isolation.md`. Verify no unexpected account membership, writable code or unit enable links. Keep private configuration/key-dependent services closed; metadata rules are not applied in this stage.

**Exit check:** exact installed inputs, unchanged system Python, inert application/vendor units, original retention intact. Version/import checks are runtime-install evidence, not production or model qualification.

## Task 5: Add the small swap buffer and close the session

**Consumes:** approved swap write and successful runtime checks, with disk and time remaining.
**Produces:** bounded swap evidence, stopped host/no temporary IP, reconciled partial failures.

- [ ] Check `/swapfile.scpilot` and the proposed fstab/sysctl marker paths are absent or exactly owned by this operation. Under root-only creation, write exactly 1,073,741,824 zero bytes into a regular single-link `0600` file without holes; verify size/allocated blocks before `mkswap`/`swapon`. On conflict or insufficient disk, stop rather than resize or reuse a foreign file.
- [ ] Preserve `/etc/fstab` and relevant sysctl originals. Add one marked swap entry and `vm.swappiness=10` in `/etc/sysctl.d/90-scpilot-swap.conf`; reject duplicate/conflicting effective settings. Verify `swapon --show --bytes`, file mode/blocks, active swappiness and remaining free space. Keep existing unit limits/concurrency and OOM handling.
- [ ] Capture package diff, ownership/path checks, all application units disabled/inactive, nftables vendor mask and the new timer state. Record swap persistence as **unverified** until an explicitly approved reboot proves it. No extra boot or capacity load is implicit in this task.
- [ ] Stop the original within the approved deadline and release the sole temporary EIP; reconcile stopped state, no public IP/allocation and encrypted original root still attached/retained. Retrieve bounded private install/recovery records before destroying any temporary helper storage.
- [ ] On failure, preserve named backups and record the exact incomplete stage. Disable no safeguards, delete no active swap and attempt no broad package rollback. If safe live `swapoff` is impossible, defer removal to a bounded maintenance/offline-root operation. Stop/release remains mandatory even when acceptance fails.
- [ ] Produce a sanitized result and update checkpoint/handoff with passed/failed/unverified checks. Do not set `production_interpreter_approved`, activate the host target, migrate real provider custody, clear reservations or merge/deploy as a side effect.

**Exit check:** stopped/no-IP custody is freshly reconciled for this future operation. Next separate acceptance work is controlled reboot/persistence, systemd252 UID/capability/metadata isolation, signed readiness and bounded capacity before actual application/public activation. Public service must explicitly replace the provisioning-only shutdown guard.
