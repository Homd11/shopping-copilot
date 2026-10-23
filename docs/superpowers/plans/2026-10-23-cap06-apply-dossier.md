# CAP-06 inactive apply dossier plan

> **For agentic workers:** Use superpowers:executing-plans inline. This is a documentation/data preparation task, with no product/runtime implementation or AWS operation.

**Goal:** Turn the existing topology, offline evidence and cost reconciliation
into a concrete proposed resource inventory and ordered rollback/teardown record.

**Architecture:** One human-readable dossier and one inert JSON inventory. Exact
proposed names/settings are distinguished from account-generated bindings, which
remain null and block apply. Existing pure access/observation renderers supply
the configuration contracts; no new renderer or apply CLI is added.

**Tech stack:** Markdown, JSON, existing Python validation/rendering APIs.

**Spec:** Existing `docs/cap04-deployment-handoff.md`, approved Stockholm amendment,
`docs/cap06-cloud-access.md`, `docs/cap06-host-services.md`, conditional observation
proposal and23October inventory reconciliation. The owner's continuation permits
preparation; no adoption, resource mutation, new paid call, upgrade or DNS write.

## Constraints and review focus

- Preserve Free plan, Stockholm, USD0cash, closed/unqualified Bedrock gate and
  non-resetting authority/allowance; no uncertain Action replay.
- Distinguish exact proposed settings from verified deployed identifiers. Do not
  substitute synthetic account/instance/distribution IDs as real bindings.
- Count all dependencies: networking attachments, two OACs, custom forwarding
  policy, both functions/log groups, runtime identities and conditional monitoring.
- Keep current selected inventory distinct from new provisioning/administration
  proposals and conditional Scheduler/metric/alarms; all remain inactive.
- Rollback must retain current accounting/identities and fence uncertain commands;
  deleting/stopping code does not stop retained resource charges.
- Production Linux build/dependency adoption and process-specific metadata access
  require further implementation/evidence, not an offline-container inference.

## Task 1: Complete the dossier

- [x] Create `docs/cap06-apply-inventory.json`: immutable constraints, proposed
      named quantities/settings, null external bindings, per-stage blocked state,
      cost scenarios, no activation and explicit remaining evidence.
- [x] Create `docs/cap06-apply-proposal.md`: binding/provisioning/secret custody,
      authority/init separation, staged activation and inverse recovery/teardown.
      Clearly state it is not yet a request for resource approval.
- [x] Check every quantity/name/reference, compare existing runtime contracts,
      use synthetic bindings only for offline renderer compatibility, independently
      recompute cost sums, validate null-blocked/no-activation states and formatting.
      No unit tests that merely mirror static JSON, no full runtime suite rerun.
- [x] One fresh read-only whole-slice review; resolve material contradictions,
      preserve known limits, update checkpoint/handoff and commit locally, no push.

Builder calls made for review, not adopted deployment changes: fixed scpilot
resource naming; one dedicated EC2 security group and owner-public-key SSH keypair
with temporary operator IPv4/32; owner copies verified release over SSH, so the
host role needs no S3 artifact/backup grant. Linux-native clean release build and
the28 runtime wheels from the tested manifest are proposed provisioning inputs.
Metadata credential isolation remains a blocking host design/verification task.
