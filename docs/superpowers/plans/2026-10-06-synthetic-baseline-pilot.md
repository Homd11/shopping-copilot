# Synthetic baseline pilot implementation

Approved scope: [pilot protocol](../../cap03-pilot-protocol.md), owner's 6 October instruction to proceed with a synthetic development pilot while leaving final evaluation open. Existing CAP-03 baseline specification supplies the model/grid/reporting contract.

1. Convert the Gemini intake as data annotations, retaining original text and source labels. Review connected conversation/paraphrase families across both batches. Keep missing-context and multi-intent exclusions explicit.
2. Add `eval/pilot_data.py`: validate source hashes, IDs, eligibility, group isolation, label order and immutable pilot split. Freeze a separate synthetic pilot release; do not overwrite the final CAP-02 unseen-release placeholder.
3. Add `eval/baseline_pilot.py`: fit the predeclared 12 TF-IDF/Logistic Regression candidates on training only; select using validation; emit predictions, metrics, plots, model and environment hashes. No runtime imports of this model and no paid LLM calls.
4. Test invalid group splits, exclusions, tampering, deterministic selection and training-only vocabulary at the offline data/model seams. Run focused checks, then repository lint/format and the full existing suites once before completion.
5. Publish a limitations-first pilot report plus rerun instructions. Retain original drafts and all trials, with final unseen evaluation and same-input LLM comparison still open. Review changes before committing only the intended files.

PDF exports, infographic and read-only AWS design preparation are separate workstreams; they do not change this experiment's inputs, runtime policies or budget.
