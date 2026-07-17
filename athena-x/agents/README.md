# agents/

All AI agents in ATHENA-X. Hierarchical organization under a single Supervisor
with 10 divisions and ~55 teams (STEP 3.5).

## Hierarchy

```
Supervisor AI
│
├── data-collection/                (Layer 1 — Provider Adapters)
│   ├── division-leader/
│   ├── market-data/                (6 collectors: Yahoo, Finnhub, Polygon, Databento, FlashAlpha, AlphaVantage)
│   ├── options-data/               (3 collectors: Polygon, Databento, FlashAlpha)
│   ├── news-data/                 (4 collectors: Reuters, CNN, WSJ, CNBC)
│   ├── macro-data/                (2 collectors: FRED, Trading Economics)
│   ├── alternative-data/          (2 collectors: SEC, Polymarket)
│   └── cross-market-data/         (20 collectors: SPY, SPX, ES, QQQ, NQ, IWM, DIA, SOXX, VIX, VVIX, MOVE, DXY, TNX, Gold, Oil, Copper, USDJPY, Europe, Asia, Crypto)
│
├── validation/                     (Layer 2 — Data Validation)
│   ├── division-leader/
│   ├── price-validator/
│   ├── volume-validator/
│   ├── options-validator/
│   ├── news-validator/
│   └── time-validator/
│
├── standardization/                (Layer 3 — Standardization)
│   ├── division-leader/
│   ├── market-standardization/    (ONLY writer to market_db)
│   ├── options-standardization/   (ONLY writer to options_db)
│   ├── news-standardization/      (ONLY writer to news_db)
│   └── macro-standardization/     (ONLY writer to macro_db)
│
├── technical-analysis/             (Layer 5 — Intelligence)
│   ├── division-leader/
│   ├── trend/                      (Trend, ADX, Support/Resistance)
│   ├── indicator/                  (EMA, SMA, VWAP, RSI, MACD, ATR, Bollinger, Stochastic, CCI, Williams-R, Ichimoku, OBV, Multi-TF)
│   ├── pattern/                    (Candlestick, Fibonacci, Elliott Wave, Escape Top, Entry, Pull-Up)
│   ├── wyckoff/
│   ├── chan-theory/
│   └── volume-price/              (Volume Profile, Volume Price, Liquidity, Smart Money)
│
├── options-intelligence/           (Layer 5 — Intelligence)
│   ├── division-leader/
│   ├── gamma/                      (GEX, Gamma Flip)
│   ├── dealer-positioning/
│   ├── iv/                         (IV, Vol Surface)
│   ├── iv-crush/                  (IV Crush, IV Rank)
│   ├── flow/                      (Option Flow)
│   ├── 0dte/
│   ├── max-pain/                  (Max Pain, Open Interest)
│   ├── greeks/
│   └── probability-of-profit/
│
├── macro-intelligence/             (Layer 5 — Intelligence)
│   ├── division-leader/
│   ├── fed/
│   ├── treasury/
│   ├── economic-calendar/
│   ├── bond-market/
│   ├── fx/
│   ├── oil/
│   ├── gold/
│   └── geopolitics/
│
├── forecast/                       (Layer 5 — Intelligence)
│   ├── division-leader/
│   ├── arima/
│   ├── lstm/                       (Python GPU — NEVER browser)
│   ├── transformer/                (Python GPU — NEVER browser)
│   ├── xgboost/                    (Python GPU)
│   ├── tabpfn/                     (Python GPU)
│   └── ensemble/                  (combines all models using dynamic weights)
│
├── decision-intelligence/          (Layer 6 — Decision)
│   ├── division-leader/
│   ├── market-regime/
│   ├── probability/               (Probability Engine, Probability Tree)
│   ├── trade-timing/              (Timeframe Sync)
│   ├── scenario-analysis/         (Scenario Analysis, AI Consensus, SPY Intelligence Aggregator)
│   └── risk-assessment/           (Expected Move, Volatility Projection)
│
├── self-validation/                (Layer 5 — Validation)
│   ├── division-leader/
│   ├── prediction-audit/
│   ├── accuracy-tracking/
│   ├── model-comparison/
│   └── self-correction/           (adjusts model_weights, updates ai_memory_db)
│
├── dashboard-reporting/            (Layer 7 — Reporting)
│   ├── division-leader/
│   ├── live-dashboard/            (pushes real-time updates to frontend)
│   ├── weekly-report/
│   ├── daily-report/
│   ├── intraday-report/           (15-min snapshots during market hours)
│   └── alert-engine/              (fires alerts on conditions)
│
└── automation/                     (RESERVED — Change 16)
    ├── division-leader/
    ├── execution/
    ├── risk/
    ├── position/
    └── broker/
```

## Layered architecture (STEP 3.5)

| Layer | Division | Rule |
|---|---|---|
| 1 | data-collection | ONLY download data, NEVER calculate |
| 2 | validation | Cross-source validation, confidence scoring |
| 3 | standardization | Convert to canonical schema, write to Layer 4 |
| 4 | (databases) | 10 separate databases — never mix |
| 5 | technical-analysis, options-intelligence, macro-intelligence, forecast | ONLY read database |
| 6 | decision-intelligence | ONLY combine information, NO calculations |
| 7 | dashboard-reporting | ONLY reads decision database |
| 8 | (frontend) | Dashboard only reads report database |

## Agent file structure

```
agents/<division>/<team>/<agent-slug>/
├── README.md
├── pyproject.toml
├── src/<pkg>/
│   ├── __init__.py
│   ├── manifest.py        # agent manifest (id, division, team, layer, subscriptions, publications)
│   ├── config.py          # Zod-validated config schema
│   ├── types.py
│   └── agent.py           # the agent class
└── tests/
```

## Reporting chain

```
Agent → Team Leader → Division Leader → Supervisor
                                        ↓
                                  (conflict detection,
                                   retry, confidence
                                   weighting, learning)
```

Heartbeats flow upward. Decisions flow downward. Events flow on the bus.

## Supervisor responsibilities (Change 3)

- Detect conflicting signals across divisions
- Check stale data (last update > threshold per asset class)
- Detect failing agents (no heartbeat in N seconds)
- Trigger retries (max 3, exponential backoff)
- Confidence weighting (dynamically adjusted based on accuracy from Self-Validation Division)
- Delegate report generation (to Dashboard & Reporting Division)
- Run self-learning (consumes lessons from ai_memory_db)
- Track performance statistics (per-agent throughput, accuracy, latency)
