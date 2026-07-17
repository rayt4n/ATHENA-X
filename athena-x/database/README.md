# database/

12 Postgres schemas (10 institutional + 2 infrastructure) per STEP 3.5.

## The 10 Institutional Databases (Layer 4)

| # | Schema | Layer | Writer | Purpose |
|---|---|---|---|---|
| 1 | `market_db` | 4 | standardization.market | Validated + standardized market data (quotes, bars, trades) |
| 2 | `options_db` | 4 | standardization.options | Validated + standardized options data (chains, greeks, IV) |
| 3 | `news_db` | 4 | standardization.news | Validated + standardized news (headlines, sentiment, entities) |
| 4 | `macro_db` | 4 | standardization.macro | Validated + standardized macro (indicators, yields, FX, commodities) |
| 5 | `validation_db` | 4 | validation agents | Validation decisions + quality scores |
| 6 | `ai_db` | 4 | intelligence agents (each owns its tables) | TA signals, options signals, news signals, macro signals, cross-market signals, regime classifications |
| 7 | `forecast_db` | 4 | decision agents | Forecast trajectories, scenarios, expected moves, probability trees, AI consensus |
| 8 | `historical_db` | 4 | report-engine + validator-engine | Reports + backtests |
| 9 | `market_replay_db` | 4 | market-replay-recorder | Minute-by-minute cross-domain snapshots (NEW) |
| 10 | `ai_memory_db` | 4 | self-correction agents | Predictions + outcomes + lessons learned (NEW) |

## Infrastructure schemas

| Schema | Purpose |
|---|---|
| `raw_landing` | Layer 1 raw payloads (provider output as-received) |
| `app` | User workspaces, watchlists, module instances |

## Critical rules

1. **Never mix raw and processed data** — raw goes in `raw_landing`, processed goes in domain databases.
2. **Each database has exactly ONE writer** — enforced by RLS.
3. **Every row carries a `confidence` column** (0.0–1.0) — confidence scoring from Layer 2.
4. **Read access is open** to authenticated users (subject to user RLS).
5. **Writer access is locked** to the designated agent per schema.
