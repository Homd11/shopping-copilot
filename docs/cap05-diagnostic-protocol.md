# CAP-05 first Bedrock diagnostic

**20 October 2026 — prepared; inference authorization pending.** The owner said
to continue with account/model verification and qualification preparation. This
document proposes one diagnostic only, not an approved paid run or a full set.

## Verified access

The owner opened ordinary Stockholm CloudShell and ran the read-only Bedrock
availability API. It returned AUTHORIZED plus AVAILABLE agreement, entitlement
and Region. A local SDK call after browser login independently returned the same
four statuses for openai.gpt-oss-20b-1:0 in eu-north-1. Neither check invoked a model
or created/accepted an agreement.

AWS CLI2.38.2 is installed for the current Windows user. The official current-user
MSI has valid Authenticode, Amazon Web Services, Inc. signer organization and a
DigiCert issuer, verified before execution. Installation returned0. The owner
completed browser sign-in to profile cap05-stockholm. SDK login uses the optional
CRT package; boto3/botocore remain1.43.115 and awscrt0.36.0 is installed. Login
caches stay managed by AWS tooling outside the repository. No access keys were
created or pasted, no active provider changed, and no account upgrade occurred.

For reproducible local SDK login support, use the optional evaluation setup:

```text
python -m pip install -r eval/requirements-bedrock.txt
```

This extra is separate from base application dependencies; an eventual EC2 role
does not require browser-login credentials. Current-source references and rate
evidence are in the [access research](research/2026-10-20-cap05-access-preflight.md).
CloudShell has its AWS-managed environment/home state; it is not application
infrastructure deployment or proof of public IPv4 credit coverage.

## Concrete proposed run

| Input                                  | Fixed value                                      |
| -------------------------------------- | ------------------------------------------------ |
| Model / Region                         | openai.gpt-oss-20b-1:0 / eu-north-1              |
| API / profile                          | Converse / cap05-stockholm                       |
| Case                                   | Exposed existing corpus ar-01, Egyptian Arabic   |
| Request                                | عاوز كوتشي جري أسود تحت 2500 جنيه                |
| Prompt / schema                        | intent-v32 / StructuredIntent9                   |
| Temperature / output limit             | 0 /1536tokens                                    |
| Actual model attempts / SDK retries    | At most1 /0                                      |
| Proposed additional AWS-credit ceiling | USD0.02 for this diagnostic only                 |
| Conservative reservation               | USD0.015 retained even on failure/cancellation   |
| Cash/account plan                      | USD0 cash constraint; keep Free plan; no upgrade |

The full128Kinput/16Koutput model-capacity envelope at the fresh Stockholm regular
on-demand list rates (USD0.07/M input, USD0.30/M output) is USD0.01409024. The
USD0.015 reservation rounds that upward, though the request itself is far smaller.
The price/API reasoning evidence is dated and conditional, not an AWS billing cap
or verified invoice. There are no cache checkpoints, tools, guardrail services,
priority/flex tier selection, subscriptions or automatic provider fallbacks.

The utility defaults to preparation only:

```text
python -m eval.bedrock_diagnostic prepare
```

It prints and stores a plan with fixed case/model/configuration and source,
request and corpus hashes, without constructing a credentialed client or creating
a spending ledger. Owned output is outputs/cap05-bedrock-diagnostic-001/.

Only after explicit owner approval may the agent use the run subcommand with an
approval reference. It exclusively creates claim.json, initializes a USD0.02
ledger once, reserves USD0.015 and makes at most one provider entry. Existing
claim/ledger or changed plan prevents ordinary rerun/reset. A crash before the
provider call can still consume the claim; it never silently retries. Do not
delete state to regain authorization.

Results store configuration/hashes, normalized metadata, latency, safe exception
category and a local schema/semantic check. Local scoring reuses the existing
corpus evaluator through a ScriptedLLMClient; even a validation repair cannot
make another real call. There are no browser Actions or shopping mutations.
Raw provider text, prompts, reasoning, credentials and error bodies are excluded
from the report. Token-derived cost is labelled estimated; cost_usd remains null
and the full reservation remains charged locally.

Stop after the one attempt. If output is truncated, invalid, denied or otherwise
fails, preserve the failure and inspect before proposing any further request.
Success is one diagnostic result, not strict model or browser qualification.

## Later qualification, separately bounded

The frozen intent-corpus-v1 contains60cases, including22critical cases repeated
three times:104scheduled attempts before any repairs. Exact request construction
at current conservative byte reservations totals USD0.28261451 without repairs;
the largest individual reservation is USD0.00273034. These are preparation
calculations, not measured usage or approval. Do not run the existing generic
benchmark unguarded or reuse the old provider-specific Gemini/OpenRouter launcher.

A subsequent full-set proposal must bind the unchanged scoring/corpus hashes,
finite repairs/attempts, durable allowance, model settings, failure preservation
and interruption semantics. Keep100%schema/currency/safety and at least95%exact
intent-and-Constraint accuracy, with repeatable critical cases. Advice/44milestone
flows and released synthetic evaluation must be reported separately; reused
synthetic data does not become independent unseen human evidence. No prior
OpenRouter approval or USD11 architecture allocation authorizes this run.

Public IPv4 coverage and remaining infrastructure permissions stay unresolved;
this model access proof does not close local02/final09/parentCAP04. CAP-05 remains
open until its actual acceptance requirements hold.
