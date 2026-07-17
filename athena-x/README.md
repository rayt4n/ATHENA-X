# ATHENA-X

> Institutional-grade quantitative intelligence terminal.
> Modular · Plugin-based · Event-driven · AI-supervised · Self-learning.

## What this is

ATHENA-X is a Bloomberg-style market intelligence platform built around
a strict layered architecture:

```
Data Collection AI → Data Validation AI → Data → Standardization AI
   → Market Data Database → Raw Intelligence Agents → Decision Intelligence
   → Supervisor AI → Institutional Validation → Report Engine → Dashboard
```

Nothing enters the system without passing through the data pipeline.
The dashboard never calculates — it only displays.

## Repository layout

| Directory | Purpose |
|---|---|
| `apps/` | Deployable applications (Next.js dashboard, Python backend) |
| `packages/` | Shared, framework-agnostic packages |
| `agents/` | All AI agents (Python) — independent, supervised |
| `engines/` | Orchestration frameworks (data, AI runtime, backtest, etc.) |
| `plugins/` | Installable indicator/pattern/options plugins |
| `providers/` | Market data provider adapters |
| `schemas/` | Single source of truth for events, DB, AI models |
| `database/` | Four logical databases (raw, processed, AI, reports) |
| `runtime/` | Bus, queue, scheduler, health, logging, metrics |
| `docs/` | Architecture, ADRs, runbooks |
| `tests/` | Cross-cutting e2e/load tests |
| `scripts/` | Dev/utility scripts |
| `tools/` | Internal scaffolding tooling |
| `configs/` | Environment-specific configs |

## Status

**STEP 3** — folder skeleton. No feature implementation yet.

See `docs/architecture/STEP-2-REVISED.md` for the full architecture specification
and `docs/architecture/implementation-order.md` for the STEP 4 plan.

## Quick start

```bash
# Frontend (Next.js dashboard)
cd apps/nextjs-dashboard && pnpm install && pnpm dev

# Backend (Python FastAPI)
cd apps/python-backend && uv sync && uv run uvicorn main:app --reload

# Or use the workspace scripts
./scripts/setup-dev.sh
```

## License

Proprietary. © 2026 ATHENA-X.
