# 08 — Locate cart and order-history destinations

**What to build:** Distinguish locating from activating while supporting cart, checkout, account, and newest-order guidance with safe authentication handoff.

**Blocked by:** 04 — Evaluate the first complete browser flow.

**Status:** ready-for-agent

- [ ] “Where is” requests Spotlight the relevant element and stop without activating it.
- [ ] Explicit “open” or navigation requests move to the requested destination.
- [ ] The Shopper can reach fictional account order history and Spotlight the newest order.
- [ ] A logged-out account route pauses and asks the Shopper to authenticate directly.
- [ ] Credentials and one-time codes are never read or entered by the Copilot.
- [ ] Evaluation Cases distinguish locate, navigate, authenticated, and logged-out behaviour.
