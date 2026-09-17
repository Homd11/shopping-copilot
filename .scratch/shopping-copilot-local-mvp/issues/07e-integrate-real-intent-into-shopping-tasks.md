# 07E — Integrate real intent into Shopping Tasks

**What to build:** Make the pinned real model the local development interpreter while preserving deterministic fast paths, task control, recovery, and every existing safety invariant.

**Blocked by:** 07D — Benchmark and select the NVIDIA model.

**Status:** ready-for-agent

- [ ] The live Agent uses validated model intent rather than hardcoded vocabulary for unfamiliar Shopper wording.
- [ ] Completely understood Constraints still use one deterministic direct-navigation fast path after validation.
- [ ] Provider failure pauses the same task with visible Retry and Stop choices; it never silently changes provider or falls back to the scripted client.
- [ ] The Panel shows honest staged status while interpretation is pending and keeps Stop available without fake progress percentages.
- [ ] Retrying creates a new model-call identity while preserving normalized task state and never replaying an uncertain browser Action.
- [ ] Ordinary tests and CI remain network-free; recorded real-model browser evaluation requires explicit opt-in and records provider metadata.
- [ ] Three previously unseen owner-written requests—one Egyptian Arabic, one Franco-Arabic, and one mixed-language—complete through the browser without adding their wording to a keyword list.
- [ ] Existing deterministic browser, refresh, lease, Stop, stale-result, currency, and safety regressions remain green.

## Comments

- Amazon Bedrock integration remains a later AWS ticket. It will use Bedrock Runtime Converse, rerun the same corpus, and leave schemas, prompts, policy, tasks, and browser contracts unchanged.
