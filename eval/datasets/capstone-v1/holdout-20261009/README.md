# Frozen synthetic test release — 9 October 2026

This is the owner-approved CAP-02 synthetic benchmark release, not an independently
collected human or scenario-family-independent unseen test set. The split is **210
existing training / 53 existing validation / 120 new synthetic test messages**.
Training and validation are referenced unchanged in the 7 October pilot release.

- Ten intent labels, four language groups, three test cases per cell.
- 44 within-test related-family groups; all their records remain in test.
- New texts are excluded from fitting, model selection and prompt tuning. Shared
  shopping capabilities/scenario semantics remain across development and test.
- Author: separate AI author. Review: coordinator AI reviewed every saved draft
  before predictions. A further reviewer failed due to usage limits; no completed
  review or human validation is attributed to that failed attempt.
- The lexical audit compared 120 messages against 2,199 strings from 169 accessible
  development/regression/debug sources. No normalized exact duplicate was found.
  Low lexical similarity does not prove semantic independence. Private history was
  not exhaustively available. Review records explicitly retain this limitation.
- Explicit disambiguators, lengthy prose and balanced labels make these authored
  requests different from natural traffic; results may be optimistic for messy
  real conversations. This is a bounded academic comparison, not user acceptance.

`protocol.json` was committed at `f2695b1` before authoring. Dataset, review and runner
were committed at `7e20365` before any candidate predictions. `author-draft.json`
preserves original wording and first labels (JSON whitespace was formatted for Git);
`author-audit.md` also records the author's pre-format handoff hash. `records.json`
contains reviewed annotations. No primary labels changed after model predictions.

`release.json` pins the protocol, records, review, schema and overlap evidence.
The original development pilots and empty independent-test placeholder remain as
historical artifacts. Do not reinterpret either as independent evaluation evidence.
After this test is consumed, any tuning against its errors makes later reuse
exposed development evidence rather than a fresh test.

Integrity command (from repository root):

```powershell
python -c "from pathlib import Path; from eval.holdout_release import load_frozen_release; load_frozen_release(Path('eval/datasets/capstone-v1/holdout-20261009/release.json'), Path.cwd())"
```

The original live audit included ignored local diagnostic sources. A fresh clone
cannot independently re-check unavailable private files; preserve the recorded
hash inventory and disclose that limitation rather than dropping the checks.
See the closeout report for published evidence inspection and reproduction commands.
