# Shopping Copilot

An Arabic-first shopping copilot that reads semantic page snapshots and performs safe,
auditable actions on a storefront. Development follows the supplied implementation plan one
step at a time.

## Prerequisites

- Python 3.12
- Node.js 24.13.0
- pnpm 11.19.0
- GNU Make on Linux/macOS (optional on Windows)

## Setup on Windows

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.lock
pnpm install --frozen-lockfile
Copy-Item .env.example .env
```

Run the services in separate terminals:

```powershell
pnpm run store
pnpm run agent:win
pnpm run panel
```

If `pnpm` is not installed on your PowerShell `PATH`, prefix the same commands with
`corepack`, for example `corepack pnpm run store`.

Open the Panel at `http://localhost:4100`. It embeds the Controlled Storefront from
`http://localhost:4000` and connects to the Agent at `http://localhost:8000`.

The local Shopping Copilot now supports deterministic discovery in Egyptian Arabic, English,
Franco-Arabic, and mixed-language input. Good manual checks are:

- `عاوز كوتشي للجري بأقل من ٢٠٠٠`
- `Show me running shoes under 2000 EGP`
- `3ayez kootshi running ta7t 2,000 EGP`
- `عاوز black running shoes مقاس 42 تحت 2500 EGP والأرخص`
- `Show unavailable bags newest first`
- `Show me something under 1000 EGP` (asks you to choose a category)

You can also press **Stop** while a task is active, or refresh the browser during a task.
Refresh restores the conversation and reconciles the current Storefront without replaying
an Action whose outcome is uncertain. Opening the same session in another tab requires an
explicit takeover.

## Quality checks

```powershell
pnpm format:check
pnpm lint
pnpm test
pnpm build
```

Install Playwright's pinned Chromium build once, then run the seven real-browser Evaluation
Cases:

```powershell
python -m playwright install chromium
pnpm eval:browser
```

The evaluation starts isolated local services, resets the Storefront before each case, and
prints one JSON result per case with pass/fail, step count, elapsed time, and failure details.
