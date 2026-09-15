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
```

Run the services in separate terminals:

```powershell
pnpm store
pnpm agent:win
```

The store is available at `http://localhost:4000`; the agent health endpoint is
`http://localhost:8000/health`.

## Quality checks

```powershell
pnpm format:check
pnpm lint
pnpm test
pnpm build
```
