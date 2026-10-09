# Synthetic holdout closeout implementation plan

> Execute with the subagent-driven-development skill for dataset authoring/review and final code review; coordinator owns evaluation/budget orchestration.

**Goal:** Close CAP-02/03 under the approved synthetic benchmark amendment.
**Spec:** docs/cap02-cap03-closeout-plan.md; frozen protocol in eval/datasets/capstone-v1/holdout-20261009/protocol.json (commit f2695b1).
**Architecture:** An evaluation-only release validator, an offline frozen-model runner, and a budgeted single-attempt LLM runner. No runtime or classifier training changes.
**Stack:** existing Python evaluation environment, sklearn/joblib, frozen encoder, existing OpenRouter client, notebook/Matplotlib.

## Tasks

- [x] Pin seven artifact hashes, selection reports, ten labels, text-only LLM prompt/schema/settings and budget before dataset authoring.
- [ ] Author 120 v2 synthetic records, three per label/language cell. Record realistic typos, constraints, source, groups and eligibility. No candidate outputs during annotation.
- [ ] Separate AI reviewer checks every label and groups. Coordinator adjudicates disagreements and runs overlap audit against accessible development/regression sources. Preserve draft/review history. Freeze records and release hashes before evaluating any contender.
- [ ] Implement release/hash/budget validation with tests for tampering, missing cells, duplicate IDs/text, group leakage, unknown cost and interrupted calls. Save a durable reservation before every paid request. Settle known usage; hold full reservation if unknown. No hidden retries or repeated attempted case on resume.
- [ ] Evaluate existing hash-verified artifacts locally. One warm-up outside test, then one message at a time; embedding timing includes encoder. Preserve failures and startup/hardware data.
- [ ] Evaluate fixed LLM once per test case, sequentially, within $0.20 and existing $2 cap. Never tune or re-label after outputs. Persist safe metadata; no credentials or private configuration.
- [ ] Produce results, figures, reproducible notebook and amended CAP-02/03 closeout documents. No generalisation or independent-human claims.
- [ ] Focused checks, review, relevant full checks, secret-safe commit. Do not push or deploy.

## Review focus

All seven models must receive exactly the same eligible messages as the LLM. Hash mismatch must stop before loading artifacts or making calls. Unknown API costs consume reservations; interrupted attempts never replay automatically. Invalid outputs remain denominator failures and confusion-matrix failure column entries. Labels and settings cannot change after predictions. Existing frozen releases and notebook evidence must be preserved.

## Decisions / evidence ledger

- Owner approved revised synthetic scope and $0.20 maximum on 2026-10-09; original independent-human requirement superseded for ticket closure, retained as limitation.
- Seven original artifacts verified in D:/agent depi/outputs; read-only loading permitted, no untrusted joblib downloads.
- Dataset author/reviewer are AI agents, not independent human contributors.
