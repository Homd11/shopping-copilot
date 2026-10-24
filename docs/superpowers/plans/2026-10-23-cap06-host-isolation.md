# CAP-06 host isolation implementation plan

> **For agentic workers:** Use superpowers:executing-plans inline; one final fresh review. Steps use checkboxes.

**Goal:** Prepare enforceable separate service credentials/config/state, a required
metadata firewall boundary and private bounded lifecycle diagnostics.

**Architecture:** Minimal per-component settings replace full Agent configuration
for native launchers. Standard-library protected I/O is shared; root metadata
helper verifies its release/UID before fixed nft exec. Unit templates bind to it
and use safe lifecycle-log hooks. Legacy local runtime remains unchanged.

**Tech stack:** Python3.12, pytest, systemd252 templates, nftables1.0.4 candidate,
retained AL2023/Python3.12 and optional isolated Ubuntu netns proof.

**Spec:** `docs/superpowers/specs/2026-10-23-cap06-host-isolation-design.md`.

## Constraints / review focus

- No actual account/user/permission/firewall/service/DNS/model activation or spend.
- Config split must not cause Store/proxy to read Agent config/key/ledger, nor
  remove fixed release/origin/version/private-file checks.
- Catalogue/WAL group read must not grant Agent writes or cross-service secrets.
- nft is own-table/chain only, fixed literals and UID, fail-closed atomic update;
  application dependency cannot claim the barrier effective if its helper failed.
- Diagnostic records cannot accept untrusted strings, follow links, exceed fixed
  retention/size or mask failure; process lifecycle is not readiness.

## Task1: Minimal settings and service boundary

- [x] Write/observe RED component schema/type/key-read tests and unit UID/write
      paths; implement host_files shared helpers, component_config and launcher split.
- [x] Update existing component/native integration tests to use minimal settings;
      keep new tests proving old full HostSettings is rejected and proxy reads no keys.
- [x] Prepare separate UID/config/state units and catalogue group/RO boundary;
      document provisioning/secret copy/ownership rather than auto-migrating state.

## Task2: Metadata helper and durable diagnostics

- [x] Write/observe RED root/release/UID/fixed subprocess/no-side-effect tests;
      implement pure nft renderer/root helper and fail-closed unit dependency.
- [x] Write/observe RED logger strict events, bounded files/retention and unsafe
      input refusal; implement fixed CLI and descriptor-safe Linux I/O/locking.
- [x] Wire pre/post hooks/private log directories, package new metadata unit and
      update production/native probe/test contracts. No native command override.

## Task3: Evidence and review

- [x] Build fresh production artifact; run default-reader/native restart probe
      and actual multi-UID DAC/logger proof in isolated Linux; attempt bounded private
      fake-metadata namespace proof with verified public test tools if needed.
- [x] Run affected full Agent/host/config/lifecycle/admission/package/release/
      browser safety suite and relevant Ruff/pip/TS lint/format/build checks.
- [x] Fresh read-only whole-slice review, one material fix pass, explicit limits
      and updated checkpoint/handoff/apply dossier. Commit locally; preserve worktree.

Interfaces: load_component_settings(path,component,read_private=...) returns only
StoreSettings or ProxySettings; command(settings,component) validates exact match.
host_metadata.render_metadata(int)->str and main(argv)->int; config schema exact
four fields from spec. host_diagnostics.record(service,event)->None, main(argv)->int
uses fixed paths; internal writer may accept explicit path/time/bounds for tests
only, no public path/free-message CLI. Re-export old private helpers to preserve
existing HostSettings/test imports. No new AWS service/inventory/spend selection.
