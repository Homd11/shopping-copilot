# CAP-01: graduation deliverables and ownership

Prepared: 2026-10-01. State: in progress following local-MVP closure; team roles supplied, remaining submission inputs being reconciled. No submission, external message or cloud provisioning has occurred.

## Goal and boundaries

Turn the approved Controlled Storefront AWS graduation scope into a concrete responsibility, deadline and evidence register. CAP-01 is planning and traceability, not model training or a new application feature. CAP-02 collects/reviews/releases the multilingual dataset; CAP-03 trains the offline TF-IDF + Logistic Regression baseline and compares intent classification with the LLM using the same eligible inputs. Runtime shopping decisions remain with the LLM and deterministic action guards.

## Evidence available

| Deliverable                        | Current evidence                                                                            | Work needed for submission                                                                       |
| ---------------------------------- | ------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| Problem, requirements and scope    | `CONTEXT.md`, local specification, README and MVP results                                   | Align wording with the actual rubric and accepted proposal.                                      |
| User motivation and evaluation     | Informal Ticket 16 findings and explicit scope adjustment                                   | Present qualitative observations and limitations; do not claim a formal study.                   |
| Technical implementation and tests | Versioned application, regression suites, frozen Ticket 15 live reports, final advice check | Pin release/configuration references and explain historical versus current evidence.             |
| ML methodology                     | Prepared dataset/baseline protocols; existing exposed development cases                     | CAP-02 reviewed release, then CAP-03 training/comparison and error analysis.                     |
| Architecture and cloud delivery    | Current local boundaries; approved Controlled Storefront direction                          | CAP-04 reviewed architecture/budget, CAP-05 qualification, CAP-06 deployment, CAP-07 acceptance. |
| Literature review                  | Questions and source-record template prepared in the local Milestone 1 draft                | Verify primary sources and synthesize relevance before submission.                               |
| Individual contributions           | Git history and task evidence                                                               | Map real agreed owners to work and maintain weekly records.                                      |
| Presentation and demonstration     | Working local application                                                                   | CAP-08 submission, AWS demo, limitations and member explanations.                                |

## Team responsibilities supplied by the owner

The owner supplied the team allocation table on 2026-10-01. Names and responsibilities reflect that table; contact addresses are excluded from the public repository. Assigned responsibilities are not claims that future deliverables are already complete.

| Member        | Assigned role                        | Responsibilities and deliverables                                                                                |
| ------------- | ------------------------------------ | ---------------------------------------------------------------------------------------------------------------- |
| Ahmed Yasser  | AI Agent & LLM Architecture          | Provider-neutral LLM client, prompt engineering, Structured Intent schema and deterministic safety boundaries.   |
| Ali Amr       | AWS Cloud Architect & Infrastructure | Bedrock Runtime integration using Converse API, hosting architecture, budget monitoring and deployment security. |
| Mohamed Hamdi | Backend & Agent Orchestration        | FastAPI session management, Server-Sent Events, action-planning lifecycle and recovery-state reconciliation.     |
| Ezz Mohamed   | Frontend & Storefront Integration    | TypeScript Bridge and Panel, cross-origin communication, responsive UI and RTL localization.                     |
| Rana Ali      | QA, Safety & Evaluation Runner       | Playwright suites, multilingual intent benchmarking and safety-invariant validation reports.                     |

The table does not separately assign submission coordination, literature-review ownership, CAP-02 unseen-data custody or CAP-03 classical-model training. Keep those gaps explicit until the team allocates them. Weekly evidence should link actual artifacts rather than attributing previous commits solely from role titles.

## Confirmed DEPI schedule

The owner supplied the Project Documentation Guidelines screenshot and explicitly selected **DEPI**, not DEPI Industry, on 2026-10-01. These are the applicable dates; the Industry column is not this team's schedule.

| Deliverable                              | Confirmed deadline |
| ---------------------------------------- | ------------------ |
| Project Planning & Management            | 16 October 2026    |
| Literature Review                        | 16 October 2026    |
| Requirements Gathering                   | 16 October 2026    |
| System Analysis & Design                 | 6 November 2026    |
| Implementation (Source Code & Execution) | 30 November 2026   |
| Final Presentation, Testing & Reports    | 4 December 2026    |

The immediate target is the three documents due **16 October**. Their content can use the completed local MVP and honest qualitative findings while describing later dataset, model-comparison and cloud work as planned. This schedule does not require inventing completed ML experiments or AWS deployment for that first deadline. The supplied schedule confirms dates, not submission templates or assessment weights.

## Remaining planning inputs

| Input                                                      | Current state                                                             | Next action                                                                      |
| ---------------------------------------------------------- | ------------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| Applicable schedule                                        | Confirmed: DEPI, dates above                                              | Use these dates in the deliverable register.                                     |
| Team members and agreed responsibilities                   | Five roles supplied above                                                 | Resolve academic coordination, dataset custody and classical-training ownership. |
| First submission deadline, required template and location  | Deadline confirmed as 16 October 2026; template and location not supplied | Obtain the required format/location without delaying the internal drafts.        |
| Official assessment weights and custom-proposal acceptance | Not independently verified                                                | Record authoritative evidence or mark pending.                                   |
| AWS-specific training/tooling requirements                 | AWS track stated by owner; detailed requirements unconfirmed              | Clarify mandatory versus optional deliverables.                                  |
| Cloud budget/credits and region                            | Not authorized for provisioning                                           | Establish a separate budget before CAP-04/06 spending.                           |

The owner supplied both the team allocation and the schedule, then explicitly selected DEPI. This record supersedes older local notes that described team roles or the schedule as unconfirmed. No contact addresses, guessed dates or claims of instructor approval are added.

## First work after those inputs

1. Finalize owners for the three 16 October documents and map each to its source evidence; technical role ownership is already recorded above.
2. Map the Milestone 1 draft into the official template; keep missing literature or rubric items explicit.
3. Create the first weekly contribution rows from actual artifacts and verification.
4. Review the submission checklist against confirmed requirements, then hand dataset work to CAP-02. CAP-03 begins only after reviewed data and splits exist.

CAP-01 closes when confirmed deliverables have actual owners, applicable deadlines and evidence references, with unresolved external requirements explicitly recorded for instructor review. Preparing this register does not mean those human inputs have been obtained.
