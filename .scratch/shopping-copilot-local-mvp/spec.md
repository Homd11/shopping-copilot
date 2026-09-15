# Shopping Copilot Local MVP

**Status:** ready-for-agent

## Problem Statement

Online shopping is difficult when a Shopper knows the outcome they want but cannot efficiently translate it into a Storefront's navigation, filters, cart controls, checkout flow, or order-history structure. This burden is greater for Egyptian Arabic, Franco-Arabic, mixed-language requests, mobile layouts, and people with limited confidence using digital interfaces.

Conventional browser agents also create unacceptable risk when they expose sensitive values, follow instructions embedded in page content, repeat stale Actions, or perform destructive and terminal changes without clear Shopper control. A useful Shopping Copilot must therefore prove both task effectiveness and visible, deterministic safety before the project expands to independent storefronts or production infrastructure.

## Solution

Build an Arabic-first Shopping Copilot for one Controlled Storefront in Chromium. A Shopper communicates through a panel using text or browser-provided speech input. The Copilot interprets the request, observes a compact semantic Snapshot, and performs one visible Storefront Action at a time. It may navigate, filter, search, locate controls with Spotlight, and manage a fictional cart and checkout flow.

The Controlled Storefront provides deterministic bilingual data and deliberately difficult interaction patterns. The Copilot treats Storefront content as untrusted, blocks off-origin navigation, never handles Sensitive Field values, rejects stale or duplicate Actions, and hands control back whenever it cannot proceed safely.

Reversible Mutations use optimistic Storefront updates with a localized Undo opportunity. Guarded Mutations—explicit bulk cart clearing and checkout submission—require a fresh, exact, single-use Confirmation. Refresh recovery restores the active Shopping Task without replaying an Action whose outcome is uncertain.

The local MVP is complete only when three recorded full-suite runs each pass at least 40 of 44 Evaluation Cases, every safety case passes on every run, performance and step targets are met, and five people complete the headline study tasks without coaching.

## User Stories

1. As an Arabic-speaking Shopper, I want to describe a shopping goal in Egyptian Arabic, so that I can shop without translating my intent into interface terminology.
2. As an English-speaking Shopper, I want to use English throughout the experience, so that the Copilot is useful without Arabic input.
3. As a Shopper who writes Franco-Arabic, I want the Copilot to understand common transliterated requests, so that I can write naturally.
4. As a bilingual Shopper, I want mixed Arabic and English phrases to work, so that product names and constraints remain accurate.
5. As a Shopper, I want responses to follow my dominant language and script, so that the conversation feels coherent.
6. As a Shopper, I want Arabic-Indic and Latin digits to be interpreted consistently, so that price and size constraints are not misunderstood.
7. As a Shopper, I want the panel to use RTL layout when appropriate, so that Arabic content remains readable.
8. As a Shopper, I want product names to remain untranslated when translation would reduce accuracy, so that I can recognize catalogue items.
9. As a Shopper, I want the Copilot to ask a concise clarification when a term maps to several categories or attributes, so that it does not guess incorrectly.
10. As a Shopper, I want overwhelmingly clear terminology to proceed without an unnecessary question, so that simple tasks remain fast.
11. As a Shopper, I want to filter products by category and use, so that I can narrow the catalogue to relevant items.
12. As a Shopper, I want to set inclusive maximum and minimum prices, so that results respect my budget.
13. As a Shopper, I want to filter by size, color, and other deterministic catalogue attributes, so that results match my needs.
14. As a Shopper, I want “cheapest” and “newest” treated as ordering preferences rather than eligibility rules, so that valid matches are not removed.
15. As a Shopper, I want a clear empty state when no products match, so that the Copilot never invents results.
16. As a Shopper, I want the Copilot to offer one named constraint to relax, so that I can continue from an empty result deliberately.
17. As a Shopper, I want unavailable products to remain visibly unavailable, so that I do not mistake them for purchasable items.
18. As a Shopper, I want unavailable products protected from cart Actions, so that the cart remains truthful.
19. As a Shopper, I want basic free-text product search, so that I can locate known product concepts.
20. As a Shopper, I want understood filters applied in one direct navigation when the Storefront Definition supports it, so that routine tasks are fast.
21. As a Shopper, I want the Copilot to fall back to visible controls when direct navigation does not produce the expected state, so that the task remains robust.
22. As a Shopper, I want “where is my cart?” to Spotlight the cart rather than open it, so that locating and activating remain distinct intentions.
23. As a Shopper, I want explicit navigation requests to open the requested area, so that the Copilot follows the action I actually requested.
24. As a Shopper, I want the Copilot to open my fictional order history and Spotlight the newest order, so that account navigation is demonstrated safely.
25. As a Shopper, I want authentication handed back to me, so that the Copilot never enters credentials or one-time codes.
26. As a Shopper, I want payment fields handed back to me, so that the Copilot never reads or enters card details.
27. As a Shopper, I want to add an available product to the cart without a confirmation interruption, so that ordinary shopping remains fluid.
28. As a Shopper, I want quantity increases and decreases to update optimistically, so that cart editing feels immediate.
29. As a Shopper, I want single-item removal to update optimistically, so that a reversible change does not require a modal decision.
30. As a Shopper, I want a ten-second Undo after a Reversible Mutation, so that I can restore the exact prior cart state.
31. As a Shopper, I want rapid quantity changes on one line coalesced into one Undo, so that recovery returns to the quantity before the burst.
32. As a Shopper, I want the remaining Undo time preserved across refresh, so that refresh does not grant extra time or remove an active recovery option.
33. As a Shopper, I want a failed optimistic update reverted automatically, so that the visible cart agrees with authoritative Storefront state.
34. As a Shopper, I want an explicit bulk “Empty cart” Action to require Confirmation, so that several selections cannot be destroyed accidentally.
35. As a Shopper, I want removing the only cart line to remain a Reversible Mutation, so that single-item removal stays consistent.
36. As a Shopper, I want checkout submission to require Confirmation, so that an order cannot be placed implicitly.
37. As a Shopper, I want each confirmation card to describe the exact Guarded Mutation and expected effect, so that I understand the decision.
38. As a Shopper, I want Confirmation to be single-use and action-specific, so that a generic “yes” cannot authorize another Action.
39. As a Shopper, I want unused Confirmation to expire after sixty seconds or relevant state change, whichever happens first, so that stale authorization cannot be reused.
40. As a Shopper, I want refresh to invalidate unused Confirmation, so that resumed tasks re-establish consent from current state.
41. As a Shopper, I want order submission possible only after I enter fictional payment details myself and provide fresh Confirmation, so that terminal policy is exercised without real commerce.
42. As a Shopper, I want short status narration before visible Actions, so that I know what the Copilot is doing.
43. As a Shopper, I want narration to omit hidden reasoning and technical policy details, so that status remains useful and safe.
44. As a Shopper, I want a reachable Stop control at all times, so that I can end an active Shopping Task immediately.
45. As a Shopper, I want Stop to prevent queued and later Actions from executing, so that cancellation has a reliable meaning.
46. As a Shopper, I want a stuck task to ask for direction after eight steps or repeated ineffective Actions, so that the Copilot does not loop indefinitely.
47. As a Shopper, I want blocked and timed-out Actions explained in plain language, so that I understand the next safe choice.
48. As a Shopper, I want off-topic messages redirected briefly in my language, so that they do not trigger Storefront Actions.
49. As a Shopper, I want page text treated as product data rather than authority over the Copilot, so that prompt injection cannot redirect my task.
50. As a Shopper, I want off-origin navigation blocked, so that the Copilot cannot silently leave the Storefront.
51. As a Shopper, I want Sensitive Field values absent from Snapshots, prompts, logs, and traces, so that private data is not exposed.
52. As a Shopper, I want a refresh to restore the visible conversation and current task status, so that I can continue without starting over.
53. As a Shopper, I want a pending question restored after refresh, so that the same Shopping Task can resume from my answer.
54. As a Shopper, I want a fresh Snapshot reconciled before a task resumes after refresh, so that the Copilot acts on current Storefront state.
55. As a Shopper, I want uncertain Actions never replayed automatically, so that refresh cannot duplicate a cart or checkout change.
56. As a Shopper, I want my task available for thirty minutes after browser or task activity, so that brief interruptions do not discard progress.
57. As a Shopper, I want an expired task reported clearly, so that I know a new session is beginning.
58. As a Shopper, I want only one tab to execute Actions for a task, so that two tabs cannot race or duplicate work.
59. As a Shopper, I want another tab to require explicit takeover before resuming Actions, so that control transfers visibly.
60. As a Shopper, I want “Start over” to clear the Copilot conversation without clearing my Storefront cart, so that task and commerce state remain separate.
61. As a Shopper, I want a Reconnecting state that temporarily disables new input and Actions, so that recovery cannot overlap with new work.
62. As a Shopper, I want cart state to outlive the Copilot task session, so that session expiry does not discard selections.
63. As a keyboard user, I want every panel control reachable with visible focus, so that the Copilot does not require a pointer.
64. As an assistive-technology user, I want semantic controls and announced status updates, so that the interaction state is perceivable.
65. As a mobile Shopper, I want the Copilot to handle menus, filter drawers, dialogs, delayed content, and repeated labels, so that mobile layout does not break the task.
66. As a Shopper, I want the Storefront currency taken from its definition, so that money interpretation is decoupled from agent logic.
67. As a Shopper, I want the local Storefront locked to EGP, so that the MVP remains deterministic and avoids false multi-currency claims.
68. As a Shopper using another currency, I want the Copilot to request an EGP amount rather than convert or guess, so that my budget is not silently changed.
69. As a project owner, I want deterministic browser assertions to judge success, so that the model cannot grade its own work.
70. As a project owner, I want recorded model, prompt, parameter, schema, token, latency, and cost metadata, so that evaluation results are reproducible.
71. As a project owner, I want every safety invariant tested deterministically and end-to-end, so that a high overall score cannot hide a safety regression.
72. As a project owner, I want five uncoached people—including two with limited digital confidence—to attempt the headline tasks, so that usability and trust are evaluated directly.

## Implementation Decisions

- The local MVP targets one Controlled Storefront and the current Chromium engine. Cross-browser and independent-storefront compatibility begin only after the local gate passes.
- The system retains five conceptual parts: Controlled Storefront, Bridge, Panel, Agent, and Evaluation Runner. Each part has one clear responsibility and communicates through versioned contracts.
- The Controlled Storefront starts as semantic server-rendered pages. Deliberate SPA variants are added later as stress tests without changing the product contract.
- The Controlled Storefront contains roughly sixty deterministic fictional products across four categories, with Arabic and English names and varied attributes. Accounts, orders, cart data, and payment data are fictional.
- URL-addressable filters are preferred for deterministic fast paths. The Copilot falls back to visible controls when the resulting Storefront state does not match the intended Constraints.
- A Storefront Definition supplies route knowledge, bilingual vocabulary, filter capabilities, and an ISO currency code. Currency is injected into interpretation logic; the MVP configuration is validated at startup and fixed to EGP.
- Money crosses internal boundaries as an exact decimal amount plus ISO currency code. The Storefront owns localized display formatting. Currency conversion, dynamic detection, and silent reinterpretation are prohibited.
- The v1 Snapshot, Action, and Action Result contracts are manually mirrored across Python and TypeScript while the protocol changes rapidly. Every wire object is versioned, and shared fixtures validate both implementations. Generated contracts are deferred until after the local protocol stabilizes.
- A Snapshot is a semantic representation rather than a DOM dump. It is capped at 12 kB, prioritizes visible interactive elements, drops low-value off-screen content when necessary, and marks truncation explicitly.
- Sensitive elements may appear only as minimal metadata marked sensitive. Their values are never collected. The execution layer independently refuses read or type Actions against them.
- Storefront text inside a Snapshot is framed as untrusted data. It cannot override the Shopping Task, policy, or system rules.
- The Agent performs one Action at a time, with a maximum of eight steps. Repeating the same Action without state change pauses the task and asks the Shopper for direction.
- One Shopping Task may be active per session. A new request is rejected unless it explicitly replaces and cancels the active task.
- Each Action and result carries task identity, action identity, and sequence information. Duplicate results are idempotent; stale and mismatched results cannot resume the loop.
- Stop atomically cancels the task, clears queued Actions, wakes pending waits, and prevents every later result or Action from taking effect.
- Locate requests use Spotlight and stop. Navigation occurs only when the request asks to open or move to the target.
- Reversible Mutations include adding a cart item, changing its quantity, and removing one line. They execute optimistically and create a ten-second localized Undo record containing the exact prior cart state.
- Consecutive quantity changes to the same cart line are coalesced into one Undo record. A rejected optimistic update automatically restores prior state and reports failure.
- Guarded Mutations are explicit bulk cart clearing and checkout submission. Confirmation is bound to the task, intended Action type, stable element signature, arguments, and expected effect. It is single-use and expires after sixty seconds, relevant state change, or refresh.
- Authentication, payment-card, and one-time-code entry always remain with the Shopper. Fake checkout submission may proceed only after the Shopper fills the form and supplies fresh Confirmation.
- The Agent service is authoritative for conversation and task state during the local MVP. The browser stores only opaque identifiers, event cursors, and non-sensitive display state.
- Refresh recovery reconnects to the existing session, restores visible conversation and pending UI state, supplies a fresh Snapshot, and reconciles before resuming. An Action with an uncertain outcome is never automatically replayed.
- A pending Shopper question survives refresh. Active Undo survives for its remaining duration; its timer is never restarted. Unused Confirmation does not survive refresh.
- Resumable sessions expire after thirty minutes of inactivity. Agent-service restart durability is deferred, but live event-stream reconnection must not duplicate Actions.
- A single browser tab holds the execution lease. Other tabs may display state but require explicit takeover before emitting or resuming Actions.
- Copilot session state and Storefront cart state have independent lifetimes. Starting over or expiring a Copilot session does not clear the cart.
- The panel restores conversation, task status, pending questions, and active Undo after refresh. It displays a noninteractive Reconnecting state until reconciliation succeeds or expiry is established.
- Status narration describes intended visible behaviour without exposing hidden reasoning, raw prompts, or internal policy details.
- The panel supports keyboard operation, visible focus, semantic controls, an announced status region, an always-reachable Stop control, RTL layout, and non-color-only state communication.
- Text input is the deterministic evaluation surface. Browser speech input receives a manual smoke test and does not affect the 40/44 reasoning gate.
- Full prompts and Snapshots may be logged only for the Controlled Storefront under an explicit development flag. Default logs are redacted metadata, and Sensitive Field values are forbidden everywhere.

## Testing Decisions

- Good tests assert externally observable behaviour rather than private implementation details. A test should prove what the Shopper sees, what Storefront state changed, or which safety boundary blocked an Action.
- The primary acceptance seam is the complete browser path through Panel, Agent, Bridge, and Controlled Storefront. Assertions use URL patterns, visible elements, Spotlight targets, Storefront state, or intercepted requests; model self-assessment is never evidence.
- Protocol contract tests run shared fixtures through the Python and TypeScript representations of Snapshot, Action, and Action Result, including version mismatch and invalid payload cases.
- Bridge tests cover accessible-name extraction, visibility, grouping, stable element identity within a page, truncation priority, sensitive-value exclusion, same-origin navigation, action execution, settle behaviour, and stale element handling.
- Agent tests cover intent normalization, Storefront Definition validation, exact Money handling, off-topic short-circuiting, policy classification, Confirmation binding and expiry, loop limits, cancellation, duplicate/stale result rejection, and refresh reconciliation.
- Panel tests cover localization, RTL, keyboard navigation, focus, status announcements, Confirmation, Undo, Stop, reconnect state, restored questions, and execution-lease takeover.
- Controlled Storefront tests cover deterministic catalogue filtering, sorting, availability, cart operations, exact Undo restoration, bulk clearing, fake checkout, fictional authentication, URL state, mobile controls, and deliberate interaction traps.
- Evaluation Runner tests cover isolated reset, deterministic assertions, recorded configuration, case timeouts, result reporting, and special continuity setup for refresh and reconnect cases.
- Safety policy is tested twice: deterministic tests at the policy seam and browser-level cases containing adversarial paraphrases and prompt-injection content.
- Ordinary CI uses a scripted model double so results are deterministic and cost-free. Recorded milestone evaluations use a pinned real provider, exact model identifier, parameters, prompts, and schema version.
- Each normal Evaluation Case begins with reset Storefront state and an isolated Copilot session. Refresh, reconnect, persistence, and multi-step continuity cases explicitly opt into retained state.
- The local exit gate requires three recorded full-suite runs. Every run must pass at least 40 of 44 cases and every safety case. Development may use focused subsets.
- Performance reporting separates Snapshot creation, serialization, model time-to-first-token, model total time, Action execution, and settle time. Median Action-step latency must not exceed two seconds; P50 and P95 are recorded.
- At least eighty percent of fully understood filter tasks complete in one Action. Navigation tasks have a median of no more than three Actions.
- Tokens and estimated cost are recorded per task and model configuration. The MVP observes cost rather than inventing a limit before evidence exists.
- Prior art includes the existing Storefront HTTP smoke test and Agent health-endpoint test. New tests extend those external seams rather than asserting internal call structure.
- Five people attempt the filter, cart/checkout guidance, and newest-order tasks without coaching. At least two have limited digital confidence, all sessions require consent for recording, and at least three participants report that the Copilot helped.

## Out of Scope

- Independent storefront compatibility before the local gate passes
- Cross-browser support beyond current Chromium
- Real customer accounts, orders, credentials, payment details, or commerce
- Product recommendation, personalization, or Copilot-authored ranking beyond Storefront filtering and ordering
- Wishlist, reviews, returns, cancellations, address editing, and account-profile changes
- Currency conversion, multiple runtime currencies, universal currency parsing, or external currency detection
- Generic crawling, automatic Storefront Definition extraction, or target-specific selector scripts
- Shopify, WooCommerce, WordPress, marketplace, or other platform integrations
- Durable recovery after Agent service restart
- Redis, PostgreSQL, vector databases, broad multi-tenancy, customer onboarding, and billing
- AWS deployment, production infrastructure, production observability, and production security claims
- Claims of compatibility with arbitrary third-party websites

## Further Notes

- The final implementation plan remains the execution-order reference, but this approved specification governs behaviour where older wording conflicts—especially refresh recovery, three-run evaluation, Storefront currency configuration, and the distinction between Reversible and Guarded Mutations.
- The four-week schedule is sequencing guidance rather than a reason to weaken gates. Reduce scope before reducing safety or evidence quality.
- `RESULTS.md` closes the local MVP with full evaluation results, safety outcomes, latency, step counts, model cost, interaction-trap findings, human-study findings, and the evidence-based next bottleneck.
- The next planning artifact should use tracer-bullet tickets that each deliver a narrow, independently demonstrable path through every affected layer.
