# Requirements gathering and traceability

**Project:** Shopping Copilot. **Document date:** 1 October 2026. **DEPI deadline:** 16 October 2026. **Status:** internal review draft; official format and assessment mapping pending.

**Academic lead:** Rana Ali, confirmed by the owner on 2 October 2026. The project owner coordinates the overall submission. This assignment does not assert authorship of prior work.

## Problem and stakeholders

A Shopper may know what they want but struggle to choose among products or translate a request into filters, navigation and cart controls. The project addresses both decision assistance and execution on one Controlled Storefront. It must support natural multilingual input while preserving the Shopper's control over consequential actions.

Stakeholders are the Shopper, the project team maintaining the catalogue/application, and the DEPI reviewers assessing the graduation deliverables. Team technical roles and confirmed dates are recorded in [the CAP-01 register](cap01-execution.md). The deployment is a controlled graduation demonstration with fictional commerce data, not a service connected to real retailers or payment providers.

## Elicitation sources and their limits

| Source                                                    | What it establishes                                                                                          | Limitation                                                                    |
| --------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------- |
| Owner-approved local specification and domain model       | Supported journeys, controlled scope and safety invariants                                                   | Earlier wording is superseded where later owner decisions are explicit.       |
| Informal feedback from five testers, relayed by the owner | Positive reactions to advice; two successful account navigations; demand for natural styling and comparisons | No standardized scores, complete task matrix or measured comparative benefit. |
| Owner observations and approved changes                   | Need for exact-match explanations, conversational follow-up and model-owned interpretation                   | Individual reports are not population-level research.                         |
| Runtime tests and live reports                            | Concrete observed successes, failure modes and guarded behaviour                                             | Coverage is finite and tied to recorded configurations.                       |
| Owner-supplied DEPI schedule and team table               | Applicable dates and assigned technical roles                                                                | The images do not establish official rubric weights or a document template.   |

All five testers reportedly lacked confidence choosing purchases online; this is not evidence that all had difficulty operating website controls. The recorded findings were robotic responses and insufficient comparison/decision support. UI comments were not supplied in detail and are not invented as requirements. The approved informal study and technical release exceptions are fully recorded in [Ticket 16 closeout](ticket16-closeout.md).

## Functional requirements

Priority **Must** means required within the approved graduation scope; it does not imply every future cloud or ML requirement is already implemented.

| ID    | Requirement                                                                                                                   | Observable acceptance and evidence                                                                                                           | State                                                                           |
| ----- | ----------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| FR-01 | Interpret Egyptian Arabic, Franco-Arabic, English and mixed-language shopping requests, including corrections and references. | Evaluate labelled intent/Constraints separately from completed browser tasks; report failures by language/scenario.                          | Local implementation/evidence exists; new dataset evaluation planned.           |
| FR-02 | Discover available products using explicit requirements, budget, size, colour and ordering preferences.                       | Verify catalogue eligibility; distinguish Exact Matches from Alternatives with named unmet or unknown requirements.                          | Implemented and tested locally.                                                 |
| FR-03 | Provide natural advice, relevant comparisons and concise reasons for exact matches using verified catalogue facts.            | Opinions are distinguishable from facts; absent qualities remain unknown; ask a useful question when needed without forcing a questionnaire. | Implemented; qualitative evidence and known grounding limitations recorded.     |
| FR-04 | Navigate or Spotlight the requested Storefront destination and open an identified product.                                    | Use current observed targets and same-origin destinations; do not confuse locating a control with activating it.                             | Implemented and tested locally.                                                 |
| FR-05 | Add a selected available variant, change quantity, remove a line and offer ten-second Undo.                                   | Assert exact variant/quantity and unaffected lines; Undo restores the precise prior state while its original deadline remains valid.         | Implemented; automated and recorded live checks.                                |
| FR-06 | Require fresh, bound, single-use Confirmation for bulk clearing and checkout submission.                                      | Unconfirmed, expired, mismatched or reused authorization cannot mutate state.                                                                | Implemented; current regressions and historical live evidence.                  |
| FR-07 | Support account/order guidance and newest-order Spotlight without handling sensitive login/payment fields.                    | Shopper enters sensitive values directly; agent acts only on permitted controls.                                                             | Implemented; two reported account navigations are a narrower human observation. |
| FR-08 | Support Stop, refresh reconciliation and task ownership across tabs.                                                          | Discard late/stale Actions and do not replay an uncertain mutation automatically.                                                            | Implemented and tested locally.                                                 |
| FR-09 | Offer readable chat, RTL/localization, product cards and editable speech input when the selected service is available.        | The Shopper can type when speech is unavailable and can review transcription before sending.                                                 | Implemented; paid voice currently constrained by provider-key allowance.        |

All functional requirements above are Must within supported local capabilities. They do not extend the catalogue to laptops merely because a participant used laptops as a comparison example.

## Safety and quality requirements

| ID    | Requirement                                                                                           | Verification approach                                                                                                                     |
| ----- | ----------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| SQ-01 | The LLM owns interpretation; validation must not become a shopper-language keyword/regex interpreter. | Inspect boundaries and test schema/target/quantity failures independently from live language-quality cases.                               |
| SQ-02 | Reject off-origin navigation and exclude Sensitive Field values from model context.                   | Adversarial browser and deterministic policy regressions.                                                                                 |
| SQ-03 | Validate inventory, quantity/price bounds, observed targets and exact mutation authorization.         | Public API, Bridge and Storefront regression checks, including stale and duplicate attempts.                                              |
| SQ-04 | Preserve truthful evidence and safe fallback.                                                         | Retain failures, unknown usage and original artifacts; malformed advice preserves verified cards without retry loops or mutation.         |
| SQ-05 | Measure latency, task steps and cost with explicit denominators.                                      | Separate model-inclusive time from browser execution; count repairs and do not substitute estimates for missing billing.                  |
| SQ-06 | Prevent credential and participant-data disclosure.                                                   | Keep environment files/secrets out of Git, omit personal contacts from public reports, and obtain authorization for recording/data reuse. |
| SQ-07 | Keep advice read-only and resistant to untrusted instructions in product text.                        | No executable fields/tools in advice responses; later action requests re-enter normal execution guards.                                   |

Current evidence is summarized in [RESULTS.md](../RESULTS.md). The historical 44-case full-model gate and its performance definitions remain tied to its frozen runtime. The local release uses the owner's explicit evidence exception; it does not prove every paraphrase, product claim or browser interaction is correct.

## Graduation ML and deployment requirements

| ID    | Requirement                                                              | Planned acceptance                                                                                                                                                              |
| ----- | ------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| GR-01 | Release reviewed multilingual data with provenance and exposure history. | CAP-02: documented labels, reviewer decisions, group-aware splits and an untouched evaluation set.                                                                              |
| GR-02 | Train an offline classical baseline and compare it fairly with the LLM.  | CAP-03: TF-IDF + Logistic Regression, train-only learned transforms, validation-based selection, same eligible inputs, confusion matrices and error/cost/latency analysis.      |
| GR-03 | Deploy the Controlled Storefront application on AWS.                     | CAP-04–07: reviewed budget/design, qualified model, protected deployment, operational acceptance and repeatable recovery/rollback evidence.                                     |
| GR-04 | Qualify the AWS model before relying on it for actions.                  | The approved gate retains 100% schema/currency/safety compliance and at least 95% exact intent-and-Constraint accuracy on its defined corpus; report unseen results separately. |
| GR-05 | Provide traceable academic and individual evidence.                      | Confirmed owners, deadlines, weekly contribution records and final documentation/demo aligned to the actual DEPI requirements.                                                  |

These are Must graduation requirements and remain planned beyond the completed local MVP. The offline baseline does not enter the runtime or authorize Actions. Separate evaluation of context-dependent requests avoids claiming that isolated text classification measures full conversational execution.

## Exclusions, assumptions and open questions

Excluded: arbitrary retailers, external store integrations, real transactions, multi-tenant SaaS and general production-readiness claims. AWS access, region/model eligibility and budget need confirmation before provisioning. Test fixtures and local accounts remain fictional; the current in-memory state is not assumed durable after cloud deployment.

The owner coordinates the overall submission. DEPI has not supplied an official template or submission location. The three academic document leads are now confirmed in the CAP-01 register; dataset custody, independent annotation review and training ownership remain pending. Rubric weights are also unconfirmed. Those gaps do not change the confirmed DEPI deadlines. Requirement changes should record their source, effect on implementation/evidence and explicit approval; passed tests do not silently redefine a requirement.
