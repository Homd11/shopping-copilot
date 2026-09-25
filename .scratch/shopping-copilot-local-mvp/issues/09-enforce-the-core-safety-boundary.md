# 09 — Enforce the core safety boundary

**What to build:** Block origin escapes, Sensitive Field access, unavailable-product cart Actions, and instructions embedded in Storefront content before they can affect a Shopping Task.

**Blocked by:** 04 — Evaluate the first complete browser flow.

**Status:** resolved

- [x] Every navigation is resolved against the current Storefront origin and off-origin destinations are blocked.
- [x] Sensitive Fields expose no value in Snapshots, prompts, logs, traces, or errors.
- [x] Read or type Actions targeting a Sensitive Field are refused independently of model output.
- [x] Products marked unavailable cannot be added to the cart.
- [x] Snapshot content is explicitly treated as untrusted data and cannot override Shopper intent or policy.
- [x] Adversarial visible, hidden, delayed, and accessibility-label instructions fail to redirect the Copilot.
- [x] Each invariant has deterministic policy coverage and a complete browser-level Evaluation Case.

## Comments

- 2026-09-25 architecture review: reproduced and closed additional Bridge gaps. Destination checks now use browser base-URL resolution, native form ownership, and the actual submitter (including clicks on descendants). Sensitive autocomplete token lists and password tokens are recognized; sensitive select Actions are refused at execution time. Aggregate/referenced Snapshot names exclude textarea and select contents, including sensitive options referenced by `aria-labelledby`. The direct regressions are in `bridge/tests/safety-review.test.ts`, with real-browser coverage appended to `eval/tests/test_ticket09_safety.py`. See the newest checkpoint entry for final verification. Existing unrelated working-tree changes were preserved.

- 2026-09-25: Bridge navigation, link clicks, and form submissions are checked against a pinned Storefront origin; dynamic Sensitive Field changes are rechecked before typing. Snapshot metadata for Sensitive Fields is generic, including textareas, and the v1 Action contract rejects read Actions. Disabled controls report blocked rather than false success. The Storefront rejects unavailable product additions at `/cart/items` with HTTP 409; available additions deliberately return HTTP 501 until Ticket 11 implements actual cart mutations. Browser safety regressions cover off-origin Actions, checkout Snapshot redaction, unavailable purchase, and visible/hidden/delayed/accessibility-label page instructions. Ticket 11 must retain the authoritative stock guard when it enables available cart additions.
