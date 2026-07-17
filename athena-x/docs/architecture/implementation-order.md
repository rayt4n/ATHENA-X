# STEP 4 — Implementation Order (Final, User-Approved)

> **Authoritative source**: `STEP-4-PLAN.md`
> **Approval**: "Approved with modifications" — see STEP-4-PLAN.md §0.

## The 18 stages

1. **Core Foundation** — event-bus, config, logger, health, scheduler, DI, auth, secrets
2. **Data Collection AI** ⭐ — 20 instruments + news + macro + alt data
3. **Validation AI** ⭐⭐⭐ — cross-provider, outlier rejection, confidence scoring
4. **Data Standardization** — canonical schema, UTC, normalized symbols
5. **Database Layer** — 12 schemas with RLS
6. **Event Bus** — connect everything end-to-end
7. **Technical Analysis Engine** — 23 plugins + 23 agents
8. **Options Intelligence** — 15 agents
9. **Cross-Market Intelligence** — correlate 14+ instruments
10. **News & Macro Intelligence** — Reuters/CNBC/WSJ/CNN + Fed + Treasury
11. **Forecast Engine** — ARIMA, LSTM, Transformer, XGBoost, LightGBM, CatBoost, TabPFN, Ensemble
12. **Decision Intelligence** — regime, probability, timing, scenarios
13. **Supervisor AI** — health, conflicts, confidence, recovery
14. **Self-Validation** — prediction vs outcome, auto-weight adjustment
15. **Reporting Engine** — 1-min, 5-min, intraday, weekly reports
16. **Dashboard** — display only, never calculates
17. **Backtesting** — vectorbt replay with full pipeline
18. **Performance & Optimization** — GPU, caching, indexes, latency

## Mandatory acceptance criteria (every stage)

A stage is **only complete** when ALL six pass:

1. **Functional tests** — features behave as specified
2. **Integration tests** — downstream components work correctly
3. **Data accuracy tests** — cross-checked against provider data
4. **Stress tests** — high event rates (FOMC, CPI)
5. **Recovery tests** — failover works when providers disconnect
6. **Performance tests** — latency and throughput within budget

See `STEP-4-PLAN.md` §3 for full criteria and §4 for performance budgets.

## Current status

- **Stage 1**: 🟡 In progress (implementation begins now)
- **Stages 2–18**: ⚪ Pending (will start after Stage 1 acceptance tests pass)
