# 04 — Evaluate the first complete browser flow

**What to build:** Provide a deterministic browser evaluation that resets the Controlled Storefront, runs representative Shopping Tasks through the complete system, and judges observable outcomes.

**Blocked by:** 03 — Run a Shopping Task through the Panel.

**Status:** ready-for-agent

- [ ] Each ordinary Evaluation Case starts from reset Storefront state and an isolated Copilot session.
- [ ] Cases can assert URL patterns, visible elements, Spotlight targets, and authoritative Storefront state.
- [ ] Evaluation outcomes never depend on the model grading its own response.
- [ ] A scripted model double makes the initial evaluation deterministic and cost-free.
- [ ] Results record pass/fail, step count, elapsed time, and failure details for every case.
- [ ] The first Arabic and English filter cases run through the real browser path in a CI-like command.
