# Shopping Copilot

The Shopping Copilot helps a shopper complete shopping tasks on an ecommerce storefront through natural language while keeping consequential actions visible and under the shopper's control.

## Language

**Shopping Copilot**:
The assistant that interprets a Shopper's request and helps carry it out on a Storefront.
_Avoid_: Bot, generic agent

**Shopper**:
The person asking the Shopping Copilot for help and retaining control over consequential choices.
_Avoid_: User, customer, operator

**Storefront**:
The ecommerce experience in which the Shopper browses products, manages a cart, checks out, and reviews orders.
_Avoid_: Website, target site, shop UI

**Storefront Definition**:
The authoritative description of a Storefront's known capabilities and constraints, including its vocabulary and configured currency.
_Avoid_: Site map, agent configuration, hardcoded store knowledge

**Controlled Storefront**:
The Storefront owned by this project and used to develop and evaluate the local MVP under reproducible conditions.
_Avoid_: Fake store, fixture site, our store

**Shopping Task**:
A bounded goal expressed by the Shopper that the Shopping Copilot either completes, safely hands back, or declines as off-topic.
_Avoid_: Job, workflow, prompt

**Constraint**:
A Shopper-supplied condition that narrows acceptable results, such as category, use, price, or size.
_Avoid_: Filter when referring to the Shopper's intent

**Snapshot**:
A semantic description of the current Storefront state that contains only the information needed to understand available interactions.
_Avoid_: DOM dump, page scrape

**Action**:
One proposed interaction with the Storefront in service of the current Shopping Task.
_Avoid_: Tool call, command, operation

**Spotlight**:
A visual cue that identifies a relevant Storefront element while leaving the next choice to the Shopper.
_Avoid_: Highlight, tooltip

**Sensitive Field**:
A field whose value the Shopping Copilot must neither read nor enter, including credentials, payment-card data, and one-time codes.
_Avoid_: Secret input, protected textbox

**Mutation**:
An Action that changes shopping state or commits a consequential choice.
_Avoid_: Write action, side effect

**Reversible Mutation**:
A cart Mutation whose precise prior state can be restored through Undo without further Shopper input.
_Avoid_: Safe action, unimportant change

**Guarded Mutation**:
A destructive or terminal Mutation that requires Confirmation before it may execute.
_Avoid_: Dangerous click, high-risk tool call

**Confirmation**:
An explicit Shopper decision that authorizes one specific Guarded Mutation within the current Shopping Task.
_Avoid_: Approval, consent prompt

**Undo**:
A time-limited opportunity to restore the exact shopping state that existed before a Reversible Mutation.
_Avoid_: Rollback, cancel

**Money**:
An exact decimal amount paired with the ISO currency configured by the Storefront Definition.
_Avoid_: Price number, floating-point amount
