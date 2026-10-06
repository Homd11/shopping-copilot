# Capstone dataset preparation structure

**State (6 October 2026):** CAP-02 final release remains open. The owner authorized a separate [synthetic pilot](pilot-20261006/README.md): 140 annotated drafts, 103 eligible cases frozen into 82 training / 21 validation / zero unseen. The [offline pilot results](../../../docs/cap03-pilot-results.md) are development evidence only. The owner and coding assistant remain the only active contributors; independent human review and unseen custody are unavailable. Original intake and the final split placeholder remain untouched.

**Subsequent development expansion:** [batch 002](development/synthetic-batch-002.json) adds 168 drafts, bringing the pool to 308 records / 263 primary candidates. The [review](../../../docs/cap02-expansion-review.md) records 41 provisional components and the remaining mutation-family coverage limitation. No new release is frozen; the first pilot and its reported score remain unchanged.

- `manifest.json`: hashes and counts of the exposed source corpora; not a released training dataset.
- `splits.json`: empty group assignments and a metadata-only slot for a future sealed unseen release.
- `case-template.json`: a non-evaluable annotation template. Null fields explicitly mean not annotated; it is never a sample or benchmark input.
- `exposure-inventory.json`: explicit `exposed` status for pinned development/test sources and legacy case IDs. Counts are source records, not unique utterances; no labels have been independently approved by this inventory.

The record contract and review process are in [the CAP-02 protocol](../../../docs/capstone-dataset.md). Use the [collection packet](../../../docs/cap02-collection-packet.md) and [label guide](../../../docs/cap02-label-guide.md) before ingestion. The primary classical/LLM comparison is recorded in [the graduation requirements](../../../docs/cap01-requirements.md#graduation-ml-and-deployment-requirements).

## Preparing records later

Review/import permitted source cases into versioned development records. Assign stable case, paraphrase and conversation group IDs. Fill provenance, consent/reuse permission, labels, reviewer decisions and the comparison-eligibility rationale. A record cannot enter a released split with unresolved labels or required context missing.

Keep `train`, `validation` and `regression` membership disjoint for the capstone release; the old regression corpus can remain available independently, but disclose any overlap with training when reporting its legacy scores. Do not aggregate those legacy scores with unseen results.

The evaluation custodian collects and seals unseen messages and labels outside the development checkout. The committed split file stores only count, checksum and release/custody metadata after freezing; do not put unseen text, labels or personally identifying information in this repository during development. At execution, provide an authorized local path to the sealed release without committing it. Pseudonymous custodian IDs refer to the restricted team register.

Before release, validate required fields, unique IDs, supported labels, group isolation, reviewed duplicates, permission, checksum consistency and input eligibility. No executable loader/validator or training command is claimed at this preparation stage.

See [the first synthetic development batch](development/README.md) for 40 annotated draft records and grouped split proposal, plus a separate 100-message Gemini intake awaiting mapping. Release split assignments and unseen cases remain zero.
