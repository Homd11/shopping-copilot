# OpenRouter cart evaluation

Owner authorized a paid Gemini Flash evaluation with an initial $0.25 total cap
after purchasing $5 of OpenRouter credit. Use the existing ignored local key.
Never enable auto top-up, purchase more credit or raise the key limit.

Implement at the existing LLMClient seam. Pin google/gemini-2.5-flash, disable
thinking, require structured-output support and cap provider prices at $0.30/M
input and $2.50/M output. Verify a non-resetting key limit <= $0.25 before each
paid call; reserve conservative request cost and reject oversized input/output.
No automatic retries or fallback to another model. Preserve local validation.

Run the same eight Egyptian Arabic cart cases twice, then verify live browser
add, mixed-cart quantity changes, removal, guarded clear and Undo. Preserve and
restore the owner's cart. Switch the demo only if evidence supports it.
Run the full workspace checks, Standards/Spec review and commit current branch.
Review baseline: 8bcf765. Existing unrelated untracked documents are out of scope.

## Live results

The key initially had a $100 limit, then $0.25 with daily renewal. Both configurations
were rejected before paid requests. The owner changed it to $0.25 with no reset;
the API confirmed the allowance before live execution.

**All 16 interpretation cases passed** (eight cases, two runs, intent-v15/schema6):
selected-item add, named size/color add, relative increase, absolute set, relative
decrease, named removal, the owner's colloquial bulk clear and standard bulk clear.
Local schema, semantic and evidence validation remained authoritative.

**All four live browser cases passed** through the actual OpenRouter-backed Agent:
add with size/color, change Playmaker 1→3 while the jacket stays 1, remove Playmaker
while preserving the jacket, and clear only after visible confirmation. Each of
the first three restored the exact original mixed cart via the ten-second Undo.
The bulk-clear test verified the cart stayed unchanged before confirmation.

The first browser harness attempts failed before model requests because its
navigation callback received the element argument as the route; this was fixed
and all four cases rerun. These failed harness attempts are not provider failures.

Provider key usage after acceptance was **$0.01594408** (about 1.6 cents), leaving
**$0.23405592** under the initial $0.25 key allowance. This is observed spend, not
a promise of cost or reliability on arbitrary future requests. No further credit
purchase, auto top-up or budget increase was performed.

Local ignored reports: `eval/reports/openrouter-cart-final.json` and
`eval/reports/openrouter-cart-browser.json`. Reproduction:

```
.venv/Scripts/python.exe -m eval.gemini_cart --provider openrouter --model google/gemini-2.5-flash --repeats 2
```

Browser acceptance requires all three local services, the paid provider explicitly
configured and `LLM_BROWSER_SMOKE=1`, then `python -m eval.openrouter_cart_browser`.
It changes fictional cart fixtures and restores the original lines in finally.

The demo is selected locally via LLM_PROVIDER=openrouter and
LLM_MODEL=google/gemini-2.5-flash. The previous free-Gemini daily automation is
paused because this evaluation supersedes it. The key's remaining $0.25 total
allowance stays enforced; do not raise it without owner authorization.

## Review

Standards: one report-directory setup finding, fixed before the final browser run.
Spec: no actionable findings. Both reviews were against 8bcf765 and included new
adapter, evaluation runner, tests and this plan. No unrelated refactoring added.

## Final verification

Full workspace suite passed **137 TypeScript + 359 Python tests (496 total)**,
including all deterministic browser regressions. Build, ESLint, Ruff lint/format,
changed-document formatting and diff checks passed. The existing multipart
pending-deprecation warning remains. All three demo services were restarted with
the tested OpenRouter configuration, returned HTTP 200, and the owner's original
fictional cart was restored. No credentials were committed.
