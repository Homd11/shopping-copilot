# 09 — Enforce the core safety boundary

**What to build:** Block origin escapes, Sensitive Field access, unavailable-product cart Actions, and instructions embedded in Storefront content before they can affect a Shopping Task.

**Blocked by:** 04 — Evaluate the first complete browser flow.

**Status:** ready-for-agent

- [ ] Every navigation is resolved against the current Storefront origin and off-origin destinations are blocked.
- [ ] Sensitive Fields expose no value in Snapshots, prompts, logs, traces, or errors.
- [ ] Read or type Actions targeting a Sensitive Field are refused independently of model output.
- [ ] Products marked unavailable cannot be added to the cart.
- [ ] Snapshot content is explicitly treated as untrusted data and cannot override Shopper intent or policy.
- [ ] Adversarial visible, hidden, delayed, and accessibility-label instructions fail to redirect the Copilot.
- [ ] Each invariant has deterministic policy coverage and a complete browser-level Evaluation Case.
