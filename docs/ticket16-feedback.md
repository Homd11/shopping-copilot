# Ticket 16: reported feedback and advice follow-up

Status: in progress, 2026-10-01. Ticket 15 is accepted; Ticket 16 is not closed.

## Evidence collected so far

The owner reports that five people tried the application while on calls with him. He subsequently clarified that he gave no help and let them test freely until they were satisfied. Record this as owner-reported uncoached exploration, not a measured completion rate or explicit helped response. The observations below are paraphrases of the owner's report, not verbatim participant quotations or independently recorded sessions. No transcript, task timing, per-task completion score, recording-consent record, digital-confidence classification or explicit helped/not-helped count has been supplied. Do not infer those measurements from the participant count. Relationships and names are unnecessary in the public study record.

| ID  | Reported finding                                                                                                                   | Evidence strength                                                                                     | Priority and response                                                                                                                                              |
| --- | ---------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| F01 | Conversation felt robotic; a participant wanted natural styling advice explaining why an option suits an outfit.                   | One participant's view, relayed by the owner; frequency across the other participants is unknown.     | High: introduce grounded conversational advice and relevant follow-up questions. Implemented in `16057d5`; live quality validation follows.                        |
| F02 | A participant wanted help comparing options, exploring priorities and making a decision without leaving the shopping conversation. | One participant's view, relayed by the owner; the laptop example illustrated the desired interaction. | High: explain trade-offs using verified facts in the existing catalogue. No laptop catalogue expansion. Implemented in `16057d5`; live quality validation follows. |

The owner explicitly excluded UI feedback from this improvement. Other UI comments were not supplied in detail and are not counted as separate findings. Two reported findings do not satisfy the existing ten-findings study criterion; no additional findings are invented to reach it.

## Bounded technical follow-up

The owner approved proceeding with documentation and a small live evaluation. This is an agent-run technical exploration with synthetic shopper messages, separate from the five people's feedback and any participant retest. It is not another Ticket 15 acceptance set or an unseen benchmark.

- Pin source `16057d5`, prompt `intent-v26`, intent schema 9 and advice prompt `advice-v1`.
- Use configured OpenRouter `google/gemini-2.5-flash` within the existing $1.00 total key cap, reset Never. A read-only check found $0.110512998 available before evaluation.
- Bound the exploration to eight shopper messages, sixteen provider calls (including interpretation repair), and $0.06 maximum reserved spend. Reserve the adapter's conservative $0.02 maximum per provider call; release the unused reservation only when attributable usage reports a valid cost. Unknown cost retains the reservation. Never increase the key cap or auto top-up.
- Exercise messy styling requests, preference/budget correction, comparison, unknown attributes, exclusions and a transition into an explicit cart action. Capture actual replies and exact cart state. Keep original failures; no repeated reruns until green.
- Use evaluation-owned local services and synthetic data. Keep raw reports under ignored `eval/reports/`; publish a redacted findings summary and provenance. Stop on an unintended mutation or other safety failure.

## Remaining Ticket 16 evidence

See [the live technical exploration](ticket16-advice-evaluation.md). It found an advice-to-navigation failure and semantic grounding weaknesses; the original failed run is retained. The resulting prompt/repair changes are verified offline only, pending a separately bounded live recheck. These technical findings are not additional participant quotations or proof that participants benefited.

Record which required tasks participants actually attempted, whether attempts were coached, explicit benefit responses and digital-confidence eligibility where known. Unknown observations stay unknown. Any additional measured sessions should follow the prepared protocol. A brief retest by one or two participants can assess whether advice improves the experience; it cannot retroactively fill missing original measurements.

Before closure, reconcile the findings requirement, the required participant/task outcomes and applicable post-change acceptance evidence. Until then, local-MVP tagging and substantive CAP-03 work remain queued. CAP-03 also requires CAP-02's reviewed dataset and splits.
