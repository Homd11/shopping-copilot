# Issue tracker: Local Markdown

Issues and specs for this repository live as Markdown files in `.scratch/`.

## Conventions

- One feature per directory: `.scratch/<feature-slug>/`
- The spec is `.scratch/<feature-slug>/spec.md`
- Implementation issues are one file per ticket at `.scratch/<feature-slug>/issues/<NN>-<slug>.md`, numbered from `01`
- Triage state is recorded as a `Status:` line near the top of each issue file
- Comments and conversation history are appended under a `## Comments` heading

## Skill operations

- When a skill says **publish to the issue tracker**, create the appropriate file under `.scratch/<feature-slug>/`.
- When a skill says **fetch the relevant ticket**, read the referenced Markdown file in full.
- Ticket dependencies use a `Blocked by: NN, NN` line. A ticket is unblocked when every listed ticket has a resolved status.
- Work the frontier: the first open, unclaimed ticket whose blockers are all resolved.
