# 10 — Confirm Guarded Mutations exactly

**What to build:** Require localized, expiring, single-use Confirmation for explicit bulk cart clearing and fake checkout submission while leaving ordinary navigation uninterrupted.

**Blocked by:** 05 — Control active tasks and Stop safely; 09 — Enforce the core safety boundary.

**Status:** ready-for-agent

- [ ] Policy classifies explicit bulk cart clearing and checkout submission as Guarded Mutations.
- [ ] Opening cart or checkout remains navigation and does not require Confirmation.
- [ ] A confirmation card states the exact proposed Mutation and expected effect in the Shopper's language.
- [ ] Authorization binds to the task, Action type, stable target signature, relevant arguments, and intended effect rather than a transient Snapshot identifier.
- [ ] Confirmation is single-use and expires after sixty seconds or relevant Storefront state change, whichever comes first.
- [ ] Unrelated, generic, expired, and already-consumed answers never authorize an Action.
- [ ] Fake order submission succeeds only after the Shopper enters fictional payment details directly and supplies fresh matching Confirmation.
- [ ] Adversarial deterministic and browser tests cover confirmation binding and expiry.
