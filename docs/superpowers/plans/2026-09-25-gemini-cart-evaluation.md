# Gemini cart evaluation

Owner-approved scope: add a Gemini adapter to the existing LLMClient interface and
evaluate Egyptian Arabic add, set/increase/decrease quantity, single removal and
guarded bulk clear. Keep local validation authoritative and Groq as the current
demo provider until evidence supports switching. No architecture refactor.

Agreed test seams: provider HTTP → validated structured output; Intent Boundary;
Shopping Task planning and observable cart changes including confirmation and Undo.

Use a local GEMINI_API_KEY (never reported or committed), gemini-2.5-flash baseline,
native generateContent JSON schema and the same prompt/schema as Groq. Evaluate
fixed requests repeatedly with bounded serial calls. Distinguish transport, schema,
semantic and boundary failures; record latency and usage. Do not retry invalid output.

Review baseline: 5e57d8e. Verification and results will be recorded below.

## Results and limits

The key was verified by model discovery without exposing it. Native generateContent
accepted the existing JSON Schema. Gemini 2.5 Flash ran with thinking disabled.
The initial eight-case pass showed three interpretation successes, one schema-level
business-rule rejection (discovery constraints on a cart edit), one product-target
semantic mismatch, two genuine local validation gaps and one provider rate limit.

The local gaps were the owner's `شيل الحاجة اللي فالسلة كلها` and the attached
preposition in `بواحد`. Both are now accepted with regression tests preserving
negation, exact quantity and single-line-versus-bulk protections. Prompt intent-v15
clarifies that cart edits may carry only size/color constraints and that product
targets exclude generic category words. Validation was not relaxed for bad output.

At 15-second spacing, the boundary-repair pass completed all eight requests:
six passed, with the old prompt's add-variant and target failures still present.
The final intent-v15 run passed selected-item add, named size/color add and the
owner's relative increase request. Latencies were 2.25, 3.875 and 2.327 seconds;
total tokens were 2823, 2713 and 2843. These are three observations, not an SLA.

The fourth final-run request received HTTP 429. A sanitized diagnostic confirmed
`GenerateRequestsPerDayPerProjectPerModel-FreeTier`, quota value **20**, rather than
a temporary pacing problem. No additional live requests are planned until quota
resets or the owner changes the project's billing tier. The reported short
provider RetryInfo is not evidence that a daily allowance will reset in seconds.

**Selection gate incomplete:** 3 of the planned 16 final-prompt requests passed;
the fourth was quota-blocked and the remaining 12 were not attempted. Live Gemini
browser mutation/Undo acceptance has not run. Do not switch the demo or describe
Gemini as proven reliable. Groq remains the configured provider; no credentials
or billing settings were changed.

Local ignored evidence: `eval/reports/gemini-cart-baseline.json`,
`eval/reports/gemini-cart-boundary-repair.json`, `eval/reports/gemini-cart-final.json`.
Resume with `.venv/Scripts/python.exe -m eval.gemini_cart --repeats 2`; reports
separate provider, schema, boundary and semantic failures and stop on throttling.
The next gate is real browser cart/confirmation/Undo acceptance after repeated
interpretation passes. Existing deterministic cart browser tests are not live-model evidence.

## Review

Standards: no actionable findings. Spec: one finding, now fixed: the evaluation
must reject unnecessary clarification even when operation fields match. A focused
matcher regression proves that missing/conflicting fields cannot score success.

## Verification

Full workspace suite: **137 TypeScript + 350 Python = 487 passing tests**.
Build, ESLint, Ruff lint/format, changed-document formatting and diff checks passed.
The existing multipart pending-deprecation warning remains. The demo services were
restored with the original Groq configuration and the saved fictional cart.
