# Local-system design views

Updated: **2 October 2026**. Companion to [System Analysis & Design](system-analysis-design.md) and its existing sequence, state and conceptual entity diagrams. These views describe the current local implementation after the session refactor (`7df44d9`); they do not select AWS services or invent persistent storage. Diagrams simplify interfaces for explanation; code references identify the authoritative implementation.

## Use-case view

```mermaid
flowchart LR
    S[Shopper]
    P[External model or speech provider]
    subgraph C[Shopping Copilot with Controlled Storefront]
        U1([Discover and discuss products])
        U2([Navigate or Spotlight])
        U3([Edit cart and Undo])
        U4([Confirm clear-cart or fictional checkout])
        U5([Guide account and newest order])
        U6([Stop and reconcile after refresh])
        U7([Dictate and review text])
    end
    S --- U1
    S --- U2
    S --- U3
    S --- U4
    S --- U5
    S --- U6
    S --- U7
    P --- U1
    P --- U7
```

This diagram groups the nine detailed use cases in [section 3](system-analysis-design.md#3-use-cases). Model interpretation also supports action requests; provider links above highlight the conversational/speech interfaces, not an exhaustive invocation map. Sensitive login/payment entry remains a manual Storefront interaction.

## Data flow: context level

```mermaid
flowchart LR
    S[Shopper]
    C((Shopping Copilot and Controlled Storefront))
    M[External LLM or transcription provider]
    S -->|Messages, selections, Confirmation, manual input| C
    C -->|Advice, product cards, guidance, action outcomes| S
    C -->|Bounded semantic context or explicitly recorded audio| M
    M -->|Untrusted structured proposal, advice or transcript| C
```

Manual Sensitive Field values stay within the Storefront interaction and are excluded from Agent/model context. Provider requests are made through server adapters; the provider does not control the browser.

## Data flow: detailed local processes

```mermaid
flowchart LR
    S[Shopper]
    P1((1 Panel and Bridge))
    P2((2 Agent interpretation and advice))
    P3((3 Task planning and validation))
    P4((4 Storefront execution))
    D1[(Agent process memory)]
    D2[(Catalogue fixture)]
    D3[(Storefront cart and order memory)]
    M[Model provider]
    S -->|Request and approved response| P1
    P1 -->|Message and sanitized Snapshot| P2
    P2 <-->|Bounded request and proposal| M
    D2 -->|Verified product facts| P2
    D1 -->|Conversation and product context| P2
    P2 -->|Validated Structured Intent| P3
    P2 -->|Advice and cards| P1
    P3 <-->|Task, identities, Confirmation and events| D1
    P3 -->|Action through Panel and Bridge| P4
    P1 -->|Manual shopper controls| P4
    P4 <-->|Revision, stock checks, cart effect and Undo| D3
    D2 -->|Authoritative variants and availability| P4
    P4 -->|ActionResult and fresh Snapshot through Panel| P3
    P3 -->|Progress, clarification or completion| P1
    P1 -->|Visible response| S
```

Data stores denote logical storage, not database services. The current Storefront cart is shared within its app instance; Agent session separation does not establish cart isolation. API delivery and browser execution are shown together only to keep the DFD readable; the sequence diagrams show the actual transport order.

## Activity: request to observed outcome

```mermaid
flowchart TD
    A[Receive request and current observation] --> B[Check session and tab ownership]
    B --> C[Interpret with LLM and bounded context]
    C --> D{Usable proposal?}
    D -->|No| E[Bounded repair, clarification or safe pause]
    D -->|Yes| F{Advice or catalogue response without a browser Action?}
    F -->|Yes| G[Retrieve facts and return advice or results]
    F -->|No| H[Resolve target and validate operation bounds]
    H --> I{Guarded Mutation?}
    I -->|Yes| J[Offer bound Confirmation]
    J --> K{Fresh matching approval?}
    K -->|No| L[Do not perform mutation]
    K -->|Yes| M[Issue identified Action]
    I -->|No| M
    M --> N[Bridge rechecks and executes permitted interaction]
    N --> O[Match ActionResult and inspect fresh state]
    O --> P{Outcome established?}
    P -->|No| Q[Pause or reconcile; no blind mutation replay]
    P -->|Yes| R{More steps?}
    R -->|Yes| H
    R -->|No| T[Report completion and available Undo]
```

The flow is conceptual: Stop, tab takeover and stale-result rejection can interrupt progression. Clarification is interpreted with task context; it is not a hardcoded phrase branch. Detailed actual statuses remain in the main document's state diagram.

## Classes and module composition

```mermaid
classDiagram
    direction LR
    class SessionStore {
        create(tab_id)
        get(session_id)
        begin_interpretation()
        accept_result()
        reconcile()
    }
    class SessionRegistry {
        _sessions
        create(tab_id)
        get(session_id)
        assert_lease(session, tab_id)
        takeover(session_id, tab_id)
    }
    class TaskRuntime {
        sessions
        planner
        clock
        confirmation_registrar
        record_snapshot(session, snapshot)
        require_task_origin(task, snapshot)
    }
    class Session {
        session_id
        active_task
        last_task
        events
        accepted_results
        product_context
        lease_tab_id
    }
    class ActiveTask {
        task_id
        status
        action
        model_call_id
        resolved_state
        confirmation
    }
    class SessionEvent {
        id
        event
        data
    }
    SessionStore *-- SessionRegistry : registry
    SessionStore *-- TaskRuntime : shared runtime
    TaskRuntime --> SessionRegistry : references
    SessionRegistry o-- Session : indexes
    Session o-- ActiveTask : active or last
    Session o-- SessionEvent : event list
```

Selected members only; this is not an exhaustive API listing. [SessionStore](../agent/sessions.py) explicitly calls functions in [interpretation](../agent/task_interpretation.py), [commands](../agent/task_commands.py), [results](../agent/task_results.py) and [recovery](../agent/task_recovery.py), passing [TaskRuntime](../agent/task_runtime.py). These are modules, not invented subclasses. [SessionRegistry](../agent/session_registry.py) handles lookup, 30-minute inactivity expiry and leases; [session_stream.py](../agent/session_stream.py) formats/delivers SSE. [Session records](../agent/session_state.py) hold the displayed state. No inheritance hierarchy or durable task-history store is implied.

## Physical storage and schema applicability

There is **no relational database in the local MVP**. The main design's ER view is conceptual. SQL tables, indexes, foreign-key constraints and normalization are therefore not implemented artifacts to submit as completed work.

| Implemented representation                    | Identity and relationships                                                              | Lifetime                                                                 |
| --------------------------------------------- | --------------------------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| Python `SessionRegistry._sessions` dictionary | Session ID → Session; Session references active/last task and event/result collections. | Agent memory; inactivity expiry and process restart.                     |
| Accepted-result dictionary                    | `(task_id, action_id, sequence_number)` → accepted result.                              | Session memory; identity checks reject mismatched/stale results.         |
| Catalogue TypeScript fixtures                 | Product ID, variants, explicit facts and configured Money.                              | Versioned source; loaded by Storefront.                                  |
| GuardedCart instance                          | Product/size/colour line identity, revision, Undo and fictional order data.             | Storefront app-instance memory; not partitioned by Agent session.        |
| Panel browser storage                         | Session/tab restoration metadata.                                                       | Browser-local recovery aid; not authority to replay an uncertain Action. |

If CAP-04 chooses persistence, document its actual logical and physical schema then, including ownership, keys, retention and migration/restart behaviour. A diagram requirement does not authorize adding a database merely to populate the report.

## Local deployment and component placement

```mermaid
flowchart TB
    subgraph Browser[User browser]
        Panel[Panel JavaScript]
        subgraph Iframe[Storefront document]
            UI[Storefront controls]
            Bridge[Bridge JavaScript]
        end
    end
    subgraph Host[Local development host]
        PS[Panel dev server - port 4100]
        AS[FastAPI Agent - port 8000]
        SS[Storefront server - port 4000]
    end
    Provider[Configured external model or speech provider]
    PS -->|Assets| Panel
    SS -->|HTML and assets| Iframe
    Panel <-->|Validated postMessage| Bridge
    Panel <-->|HTTP and SSE| AS
    UI <-->|Storefront requests| SS
    AS -->|Catalogue requests| SS
    AS <-->|Server-side provider adapter| Provider
```

These are local development processes, not an AWS deployment. See the main design for the logical component view and CAP-04's unresolved HTTPS, access, isolation, restart and cost decisions.

## UI wireframes and implemented guidelines

Schematic desktop layout (not a screenshot; labels indicate regions rather than a fixed language direction):

```text
+--------------------------------+--------------------------------------+
| Copilot identity / Stop        |                                      |
| Status or recovery banner      |       Controlled Storefront           |
|--------------------------------|                                      |
| Independently scrolling chat   |       Product / cart / account        |
| Advice + product cards         |       controls in its iframe          |
| Clarification / Confirmation   |                                      |
|--------------------------------|                                      |
| Language + speech + text/send  |                                      |
+--------------------------------+--------------------------------------+
```

Guarded interaction detail:

```text
+------------------------------------------------+
| Proposed effect and affected cart state        |
| Shopper can inspect the bound request          |
| [Confirm]                 [Cancel / Stop]       |
+------------------------------------------------+
```

The schematic does not imply that a label alone grants authorization; IDs, state signatures, expiry and single-use checks bind Confirmation. Ordinary reversible edits show an Undo option with its original deadline.

The implementation uses Segoe UI/Tahoma/Arial, dark text, blue emphasis, light surfaces and clear borders. The Panel has bounded viewport height, independently scrolling messages and a composer outside that scroll region. RTL/localized labels, visible focus styles, disabled/pending states, responsive layout and a typing fallback support interaction. Inspect [Panel CSS](../panel/src/styles.css), [Panel markup/controller](../panel/src/panel.ts), [entry markup](../panel/index.html) and [Storefront CSS](../store/public/store.css) for exact layouts and tokens. This documents implemented design choices; it does not claim formal WCAG conformance or measured accessibility results. Final screenshots and export layout belong in the submission package after owner review.
