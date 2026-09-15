# 15 — Pass the complete local evaluation gate

**What to build:** Complete and run the forty-four-case evaluation with reproducible model settings, mandatory safety success, and the approved task-efficiency and latency evidence.

**Blocked by:** 10 — Confirm Guarded Mutations exactly; 12 — Recover Mutation state across refresh; 14 — Preserve behaviour across SPA navigation.

**Status:** ready-for-agent

- [ ] The suite contains forty-four deterministic cases covering language, discovery, navigation, locate, mobile traps, SPA behaviour, safety, Stop, reconnect, refresh, Confirmation, and Undo.
- [ ] Ordinary CI uses the scripted model double and the milestone run pins the live provider, exact model identifier, parameters, prompts, and schema version.
- [ ] Every recorded result includes pass/fail, steps, phase latency, token use, estimated cost, and failure category.
- [ ] Snapshot creation, serialization, model time-to-first-token, model total time, Action execution, and settle time are measured separately.
- [ ] Median Action-step latency is at most two seconds, with P50 and P95 reported.
- [ ] At least eighty percent of fully understood filter tasks complete in one Action and navigation tasks have a median of no more than three Actions.
- [ ] Three full recorded runs each pass at least forty of forty-four cases.
- [ ] Every safety case passes in every recorded run.
