# 10 — Confirm Guarded Mutations exactly

**What to build:** Require localized, expiring, single-use Confirmation for explicit bulk cart clearing and fake checkout submission while leaving ordinary navigation uninterrupted.

**Blocked by:** 05 — Control active tasks and Stop safely; 09 — Enforce the core safety boundary.

**Status:** resolved

- [x] Policy classifies explicit bulk cart clearing and checkout submission as Guarded Mutations.
- [x] Opening cart or checkout remains navigation and does not require Confirmation.
- [x] A confirmation card states the exact proposed Mutation and expected effect in the Shopper's language.
- [x] Authorization binds to the task, Action type, stable target signature, relevant arguments, and intended effect rather than a transient Snapshot identifier.
- [x] Confirmation is single-use and expires after sixty seconds or relevant Storefront state change, whichever comes first.
- [x] Unrelated, generic, expired, and already-consumed answers never authorize an Action.
- [x] Fake order submission succeeds only after the Shopper enters fictional payment details directly and supplies fresh matching Confirmation.
- [x] Adversarial deterministic and browser tests cover confirmation binding and expiry.

## Progress (2026-09-25)

- Architecture review: reproduced and closed ordinary-click bypasses of the Bridge's guarded-form classification for absolute destinations, separately associated forms, native submitter method/destination overrides (including descendant clicks), and route case/trailing-slash variants accepted by the Controlled Storefront. These paths now require the same Confirmation as canonical forms. The independent Storefront token check already rejected unauthorized submissions; the finding concerned the Bridge's own enforcement. Direct and browser regressions were added; see the newest checkpoint entry for final verification. Broader Confirmation/cart module deepening remains a recommendation, not a prerequisite for Ticket 11.

- Structured Intent v4 and prompt `intent-v11` distinguish explicit bulk clear / fictional checkout submission from frictionless cart / checkout navigation. The shared Intent Boundary and Session check current Shopper source and reject negated or unsupported mutation claims. A direct import-order regression caught and removed an Agent circular import.
- The Agent issues a localized confirmation card and holds an exact, clock-controlled offer. Its one-use authority binds task, Guarded Action type, stable form target, cart revision, and expected effect; refresh invalidates an unused offer. A distinct `guarded_click` Action is emitted only after the matching card answer and current Snapshot check.
- The Bridge exposes only non-sensitive guarded form metadata, blocks ordinary clicks and submit-through-typing on controlled guarded forms, rechecks the live target/revision/form validity, and never reads card values. The Controlled Storefront also consumes a one-use, revision-bound token before bulk clear or fictional order submission. The Shopper must enter the displayed fictional card values directly. The resulting page is verified before the Agent reports success; an uncertain result is paused, never replayed.
- The cart and order state are deliberately in-memory and minimal. A test-only cart seed supports Ticket 10's browser path until Ticket 11 implements normal add, quantity, remove, and Undo. Development listeners now bind to loopback; the local registration endpoint is **not** a production authentication or payment boundary against arbitrary processes on the same machine.
- Final verification on 2026-09-25: 304 Python tests (including five Ticket 10 browser cases) and 114 TypeScript tests passed; build, Ruff lint/format, ESLint, changed-file Prettier, and diff checks passed. Two live Groq probes recognized English and Egyptian Arabic clear-cart intent; the next probe hit HTTP 429, so scripted browser success is not a claim of reliable free-tier live-model availability. No real payment, database, AWS, or Ticket 11 cart-add behavior was added.
