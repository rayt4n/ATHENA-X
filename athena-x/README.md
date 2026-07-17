# ATHENA-X

> Institutional-grade quantitative intelligence terminal.
> Modular · Plugin-based · Event-driven · AI-supervised · Self-learning.
> Strict 8-layer data pipeline (STEP 3.5).

## What this is

ATHENA-X is a Bloomberg-style market intelligence platform built around
a strict layered architecture (STEP 3.5):

```
Layer 8 ─ Dashboard            ◄── reads Report Database only
            ▲
Layer 7 ─ Report Generator     ◄── reads Decision Database only
            ▲
Layer 6 ─ Decision Agents      ◄── combine information, NO calculations
            ▲
Layer 5 ─ Intelligence Agents  ◄── EMA, RSI, MACD, Chan Theory, Wyckoff, Gamma, etc.
                                  ONLY read database
            ▲
Layer 4 ─ Institutional Database (10 separate databases — never mix)
            ▲
Layer 3 ─ Standardization Agents
            ▲
Layer 2 ─ Data Validation Agents
            ▲
Layer 1 ─ Provider Adapters    ◄── ONLY download data, NEVER calculate
```

**Nothing above Layer 1 calls providers directly.**
**Nothing above Layer 3 touches raw data.**
**The dashboard never calculates — it only displays.**

## Repository layout

| Directory | Purpose |
|---|---|
| `apps/` | Deployable applications (Next.js dashboard, Python backend) |
| `packages/` | Shared, framework-agnostic packages |
| `agents/` | All AI agents — hierarchical under Supervisor (10 divisions × ~55 teams) |
| `engines/` | Orchestration frameworks (data, AI runtime, backtest, etc.) |
| `plugins/` | Installable indicator/pattern/options plugins |
| `providers/` | 14 market data provider adapters |
| `schemas/` | Single source of truth for events, DB, AI models |
| `database/` | 12 schemas (10 institutional + 2 infrastructure) |
| `runtime/` | Bus, queue, scheduler, health, logging, metrics |
| `docs/` | Architecture, ADRs, runbooks |
| `tests/` | Cross-cutting e2e/load tests |
| `scripts/` | Dev/utility scripts |
| `tools/` | Internal scaffolding tooling |
| `configs/` | Environment-specific configs |

## Status

**STEP 3.5** — Institutional Data Layer complete. Skeleton ready.

See `docs/architecture/STEP-3.5-ARCHITECTURE.md` for the authoritative spec.

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
