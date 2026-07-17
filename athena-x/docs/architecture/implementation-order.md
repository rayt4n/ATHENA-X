# STEP 4 — Implementation Order

The 18-stage sequence (Change 20 of STEP 2.1). Each stage ships with
`tsc --noEmit` + `next lint` + `pytest` + `next build` passing.
Zero errors before proceeding to the next stage.

| # | Stage | Key deliverables |
|---|---|---|
| 1 | Foundation / Core Runtime | event-bus, logger, health-monitor, di, config |
| 2 | Data Collection AI | collection-agent, validation-agent, standardization-agent |
| 3 | Data Validation AI | (covered in stage 2 — listed separately per user spec) |
| 4 | Database Layer | 4 schemas, RLS, migrations, seeds |
| 5 | Event Bus | full bus impl + WebSocket bridge |
| 6 | Technical Analysis Engine | 23 TA agents + 14 indicator plugins |
| 7 | Options Intelligence | 15 options agents + 6 options plugins |
| 8 | Market Intelligence | macro-agent + news-agent + cross-market (20 agents) |
| 9 | Cross-Market Intelligence | spy-intelligence-aggregator |
| 10 | AI Forecast Engine | hybrid AI router (LSTM/Transformer/etc.) |
| 11 | Probability Engine | Monte Carlo |
| 12 | Supervisor AI | conflict detection, retries, confidence weighting |
| 13 | Validation AI | Institutional Validation Layer |
| 14 | Report Engine | markdown → json → pdf → storage |
| 15 | Dashboard / UI | Next.js modules, panels, palette |
| 16 | Self-Correction & Learning | prediction scoring, weight adjustment |
| 17 | Backtesting & Strategy Validation | vectorbt strategies |
| 18 | Performance Optimization | caching, batching, profiling |

## Per-stage quality gates

```bash
# TypeScript
pnpm --filter @athena-x/dashboard typecheck
pnpm --filter @athena-x/dashboard lint
pnpm --filter @athena-x/dashboard test
pnpm --filter @athena-x/dashboard build

# Python
uv run ruff check .
uv run mypy .
uv run pytest
```

All four must pass (zero errors) before the next stage begins.
