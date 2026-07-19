# STEP 3.5 — Institutional Data Layer

> The single most important architectural decision in ATHENA-X.
> This document supersedes the database + agent organization in STEP 2 / STEP 2.1 / STEP 3.

---

## 0. Core Principle

**Nothing above can calculate directly. Everything reads from the database.**

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

### Why this matters

If Yahoo fails:

```
Yahoo ❌
  ↓
Validator detects
  ↓
Switch to Polygon
  ↓
Continue
  ↓
Dashboard doesn't even notice
```

The dashboard, intelligence agents, and decision agents are completely
insulated from provider failures. They read from databases that are
always populated with validated, standardized data.

---

## 1. The 8 Layers (Strict)

### Layer 1 — Provider Adapters

**Role**: Download data from external sources. Period.

**Rule**: Never calculate. Never validate. Never standardize. Just fetch
and emit raw payloads.

**12 providers** (up from 7 in STEP 3):

| # | Provider | Asset class focus |
|---|---|---|
| 1 | Yahoo | Equity / ETF / index / currency / commodity / yield |
| 2 | Finnhub | Equity / ETF / currency (WebSocket) |
| 3 | Polygon | Equity / ETF / currency / commodity (WebSocket) |
| 4 | Databento | Institutional-grade futures / options (NEW) |
| 5 | FlashAlpha | Equity / ETF / options |
| 6 | FRED | Yield / macro indicators |
| 7 | AlphaVantage | Equity / ETF / currency |
| 8 | Trading Economics | Macro indicators — global (NEW) |
| 9 | Reuters | News (NEW) |
| 10 | CNN | News / Fear & Greed Index (NEW) |
| 11 | WSJ | News (NEW) |
| 12 | CNBC | News (NEW) |
| 13 | SEC | Filings / institutional holdings (NEW) |
| 14 | Polymarket | Prediction markets (NEW) |
| — | Simulated | DEV ONLY — never in production |

### Layer 2 — Data Validation Agents

**Role**: Every incoming data point is checked against other sources.

**Example**:
```
Yahoo    says SPY = 752.44
Polygon  says SPY = 752.46
Finnhub  says SPY = 752.45
                    ↓
            Validator
                    ↓
       Difference < tolerance (0.02)
                    ↓
              Status: Verified
```

If one source suddenly says 742 → **REJECT. Never allow into database.**

**5 validator teams**:
- Price Validator — cross-source price validation
- Volume Validator — volume sanity checks
- Options Validator — IV/Greeks/OI consistency
- News Validator — duplicate detection + source reputation
- Time Validator — timestamp normalization + staleness check

**Output**: Every validated dataset gets a **confidence score** (0.0–1.0)
stored alongside the data. Downstream agents can filter by confidence.

### Layer 3 — Standardization Agents

**Role**: Convert every provider's idiosyncratic schema into one canonical format.

| Input variation | Canonical output |
|---|---|
| `close`, `Close`, `last`, `price` | `last_price` |
| Local timezone timestamps | UTC ISO 8601 |
| Provider-specific symbol codes (e.g., `BRK.B`, `BRK-B`) | Normalized (`BRK.B`) |
| Varying decimal precision | Normalized per asset class |
| Mixed units (cents vs dollars, % vs decimal) | Normalized |

**Only writers to Layer 4 domain databases** (after Layer 2 validation passes).

### Layer 4 — Institutional Database (10 separate databases)

**Rule**: Never mix them. Each database has exactly ONE writer (a Layer 3
standardization agent or a Layer 5/6 agent writing its own outputs).

| # | Database | Writer | Reader |
|---|---|---|---|
| 1 | `market_db` | Standardization (market) | Intelligence agents (TA, Cross-Market) |
| 2 | `options_db` | Standardization (options) | Intelligence agents (Options) |
| 3 | `news_db` | Standardization (news) | Intelligence agents (News) |
| 4 | `macro_db` | Standardization (macro) | Intelligence agents (Macro) |
| 5 | `validation_db` | Validation agents | All (for confidence filtering) |
| 6 | `ai_db` | Intelligence agents (each owns its tables) | Decision agents |
| 7 | `forecast_db` | Decision agents | Report Generator |
| 8 | `historical_db` | Report Engine + Validator Engine | Dashboard |
| 9 | `market_replay_db` | Market Replay Recorder (NEW) | Backtesting, AI training, debugging |
| 10 | `ai_memory_db` | Self-Correction agents | All (for learning) |

Plus infrastructure schemas (not counted in the 10):
- `raw_landing` — Layer 1 raw payloads (provider output as-received)
- `app` — workspaces, watchlists, module instances, user data

### Layer 5 — Intelligence Agents

**Role**: Compute indicators, recognize patterns, extract signals.

**Rule**: ONLY read from Layer 4 databases. NEVER call providers directly.
NEVER calculate outside their domain.

**Agents**: EMA, RSI, MACD, ADX, ATR, Bollinger, Fibonacci, Stochastic,
Chan Theory, Wyckoff, Volume Profile, Smart Money, Greeks, IV, Gamma
Exposure, Max Pain, sentiment classifiers, macro analyzers, etc.

**Output**: Written to `ai_db` (each agent owns its own tables).

### Layer 6 — Decision Agents

**Role**: Combine information from Layer 5 outputs.

**Rule**: NO calculations. Only combine, weigh, and aggregate.

**Agents**: Market Regime, Probability, Trade Timing, Scenario Analysis,
Risk Assessment, AI Consensus, Timeframe Sync.

**Output**: Written to `forecast_db`.

### Layer 7 — Report Generator

**Role**: Compose reports from Decision Database.

**Rule**: ONLY reads `forecast_db` + `ai_memory_db` (for historical context).

**Output**: Markdown → JSON → PDF → `historical_db` → Dashboard.

### Layer 8 — Dashboard

**Role**: Display, filter, search, layout, user interaction.

**Rule**: NEVER calculates. Only reads `historical_db` (for reports) +
subscribes to bus events (for live updates pushed by Layer 6/7).

---

## 2. Market Replay Database (NEW)

**Purpose**: Store everything, every minute, for the entire trading day.

```
09:30 → { prices, volumes, options, greeks, news, gamma, dark pool, breadth, ... }
09:31 → { ... }
09:32 → { ... }
...
16:00 → { ... }
```

**Schema** (in `market_replay_db`):

```sql
CREATE TABLE market_replay_db.minute_snapshots (
    snapshot_id      BIGSERIAL PRIMARY KEY,
    timestamp        TIMESTAMPTZ NOT NULL,    -- minute boundary (UTC)
    trading_date     DATE NOT NULL,
    session          TEXT NOT NULL,           -- 'pre'|'regular'|'post'
    -- Cross-domain snapshot (each is a JSONB blob referencing other DBs)
    market_snapshot  JSONB NOT NULL,          -- quotes for all tracked symbols
    options_snapshot JSONB,                   -- chains + greeks + IV
    news_snapshot    JSONB,                   -- headlines received this minute
    macro_snapshot   JSONB,                   -- macro indicators updated
    gamma_snapshot   JSONB,                   -- GEX + gamma flip per symbol
    darkpool_snapshot JSONB,                  -- dark pool prints
    breadth_snapshot JSONB,                   -- advance/decline, new highs/lows
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_replay_date_time ON market_replay_db.minute_snapshots (trading_date, timestamp);
```

**Use cases**:
- **Backtesting**: replay any historical minute with full context
- **Training AI models**: supervised learning on labeled historical windows
- **Debugging decisions**: "what did the AI know at 10:15:32 on 2026-03-14?"
- **Improving forecasts**: compare predictions to actuals with full context

---

## 3. AI Memory Database (NEW)

**Purpose**: Store what the AI concluded, why, and whether it was right.

**Schema** (in `ai_memory_db`):

```sql
CREATE TABLE ai_memory_db.predictions (
    prediction_id    UUID PRIMARY KEY,
    timestamp        TIMESTAMPTZ NOT NULL,
    agent_id         TEXT NOT NULL,           -- e.g., 'forecast.lstm'
    model_id         TEXT,                    -- 'lstm'|'transformer'|'xgboost'|...
    symbol           TEXT NOT NULL,
    prediction_type  TEXT NOT NULL,           -- 'price'|'direction'|'regime'|'probability'
    prediction_value JSONB NOT NULL,          -- the actual prediction
    horizon          TEXT NOT NULL,           -- '1D'|'1W'|'1M'
    reason           TEXT,                    -- human-readable rationale
    evidence         JSONB,                   -- what inputs drove this
    confidence       NUMERIC NOT NULL,        -- 0..1
    -- Outcome (filled in later when the horizon elapses)
    actual_value     JSONB,
    outcome_timestamp TIMESTAMPTZ,
    error            NUMERIC,                 -- |predicted - actual|
    absolute_error   NUMERIC,
    squared_error    NUMERIC,
    -- Learning signal
    lessons_learned  JSONB                    -- what the self-correction engine derived
);

CREATE TABLE ai_memory_db.agent_performance (
    agent_id         TEXT NOT NULL,
    period           TEXT NOT NULL,           -- '7d'|'30d'|'90d'|'all'
    accuracy         NUMERIC,
    precision        NUMERIC,
    recall           NUMERIC,
    sharpe           NUMERIC,
    max_drawdown     NUMERIC,
    sample_count     INTEGER,
    computed_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (agent_id, period, computed_at)
);

CREATE TABLE ai_memory_db.lessons (
    lesson_id        BIGSERIAL PRIMARY KEY,
    timestamp        TIMESTAMPTZ NOT NULL DEFAULT now(),
    lesson_type      TEXT NOT NULL,           -- 'indicator-reliability'|'model-regime-fit'|'fomc-failure'|...
    description      TEXT NOT NULL,
    evidence         JSONB,                   -- supporting data
    applied          BOOLEAN DEFAULT false,   -- has this been wired into production?
    applied_at       TIMESTAMPTZ
);
```

**After six months you can answer**:
- Which indicators are most reliable?
- Which model performs best in trending markets?
- Which model fails during FOMC days?
- Which combinations produce the highest accuracy?

This enables **continuous self-improvement** (Change 12 of STEP 2.1).

---

## 4. Hierarchical Agent Organization

78 agents were too flat. Reorganize into 10 divisions under the Supervisor.

```
Supervisor AI
│
├── Data Collection Division               (5 teams)
│   ├── Market Data Team
│   ├── Options Data Team
│   ├── News Data Team
│   ├── Macro Data Team
│   └── Cross-Market Data Team
│
├── Validation Division                     (5 teams)
│   ├── Price Validator Team
│   ├── Volume Validator Team
│   ├── Options Validator Team
│   ├── News Validator Team
│   └── Time Validator Team
│
├── Technical Analysis Division            (6 teams)
│   ├── Trend Team
│   ├── Indicator Team
│   ├── Pattern Team
│   ├── Wyckoff Team
│   ├── Chan Theory Team
│   └── Volume/Price Team
│
├── Options Intelligence Division          (7 teams)
│   ├── Gamma Team
│   ├── Dealer Positioning Team
│   ├── IV Team
│   ├── IV Crush Team
│   ├── Flow Team
│   ├── 0DTE Team
│   └── Max Pain Team
│
├── Macro Intelligence Division            (8 teams)
│   ├── Fed Team
│   ├── Treasury Team
│   ├── Economic Calendar Team
│   ├── Bond Market Team
│   ├── FX Team
│   ├── Oil Team
│   ├── Gold Team
│   └── Geopolitics Team
│
├── Forecast Division                       (6 teams)
│   ├── ARIMA Team
│   ├── LSTM Team
│   ├── Transformer Team
│   ├── XGBoost Team
│   ├── TabPFN Team
│   └── Ensemble Team
│
├── Decision Intelligence Division         (5 teams)
│   ├── Market Regime Team
│   ├── Probability Team
│   ├── Trade Timing Team
│   ├── Scenario Analysis Team
│   └── Risk Assessment Team
│
├── Self-Validation Division                (4 teams)
│   ├── Prediction Audit Team
│   ├── Accuracy Tracking Team
│   ├── Model Comparison Team
│   └── Self-Correction Team
│
├── Dashboard & Reporting Division         (5 teams)
│   ├── Live Dashboard Team
│   ├── Weekly Report Team
│   ├── Daily Report Team
│   ├── Intraday Report Team
│   └── Alert Engine Team
│
└── Automation Division (RESERVED)         (4 teams)
    ├── Execution Team
    ├── Risk Team
    ├── Position Team
    └── Broker Team
```

**10 divisions, 55 teams total.**

### Why hierarchical?

- **Scales** — adding a new model (e.g., a new Transformer variant) is a team-level change, not a system-wide change
- **Isolates failure** — a buggy pattern agent doesn't take down options intelligence
- **Clear ownership** — each division has a leader, each team has a leader, every agent knows its reporting chain
- **Simplifies supervision** — the Supervisor talks to 10 division leaders, not 166 agents

### Reporting flow

```
Agent → Team Leader → Division Leader → Supervisor
                                        ↓
                                  (conflict detection,
                                   retry, confidence
                                   weighting, learning)
```

Heartbeats flow upward. Decisions flow downward. Events flow on the bus.

---

## 5. Expanded Provider List

8 new providers added to support the broader data scope:

| New Provider | Purpose | Layer |
|---|---|---|
| Databento | Institutional-grade futures/options data (PIT-validated) | 1 |
| Trading Economics | Global macro indicators (50+ countries) | 1 |
| Reuters | News wire service | 1 |
| CNN | News + Fear & Greed Index | 1 |
| WSJ | News (Wall Street Journal) | 1 |
| CNBC | News (financial media) | 1 |
| SEC | EDGAR filings, 13F institutional holdings | 1 |
| Polymarket | Prediction markets (event probabilities) | 1 |

**Failover chain** (unchanged from STEP 3 for market data):
```
Yahoo → Finnhub → Polygon → FlashAlpha → FRED → AlphaVantage
```

Databento is added as an institutional-grade source for backtesting/training
(not in the live failover chain by default, but available).

News providers (Reuters, CNN, WSJ, CNBC) run concurrently — the News
Validator deduplicates and ranks by source reputation.

---

## 6. Expanded Database Schema

STEP 3 had 4 schemas. STEP 3.5 has 12 (10 institutional + 2 infrastructure):

| # | Schema | Purpose | Layer |
|---|---|---|---|
| 1 | `raw_landing` | Layer 1 raw payloads | Infra |
| 2 | `market_db` | Validated + standardized market data | 4 |
| 3 | `options_db` | Validated + standardized options data | 4 |
| 4 | `news_db` | Validated + standardized news | 4 |
| 5 | `macro_db` | Validated + standardized macro | 4 |
| 6 | `validation_db` | Validation decisions + quality scores | 4 |
| 7 | `ai_db` | Intelligence agent outputs (TA, Options, News, Macro, Cross-Market signals) | 4 |
| 8 | `forecast_db` | Decision agent outputs (regime, scenarios, forecasts, probability trees) | 4 |
| 9 | `historical_db` | Reports + backtests | 4 |
| 10 | `market_replay_db` | Minute-by-minute cross-domain snapshots | 4 (NEW) |
| 11 | `ai_memory_db` | Predictions + outcomes + lessons | 4 (NEW) |
| 12 | `app` | User workspaces, watchlists, module instances | Infra |

**Writer access (RLS-enforced)**:

| Schema | Writer |
|---|---|
| `raw_landing` | Layer 1 provider adapters (any) |
| `market_db` | `standardization.market` agent only |
| `options_db` | `standardization.options` agent only |
| `news_db` | `standardization.news` agent only |
| `macro_db` | `standardization.macro` agent only |
| `validation_db` | Layer 2 validation agents (each writes its own tables) |
| `ai_db` | Layer 5 intelligence agents (each writes its own tables) |
| `forecast_db` | Layer 6 decision agents (each writes its own tables) |
| `historical_db` | Report Engine + Validator Engine only |
| `market_replay_db` | Market Replay Recorder agent only |
| `ai_memory_db` | Self-Correction agents only |
| `app` | Frontend (via Supabase Auth + RLS) |

---

## 7. Confidence Scoring (every dataset)

Every row in every Layer 4 database carries a `confidence` column (0.0–1.0).

**How confidence is computed** (in Layer 2):

```
confidence = base_score
           + source_count_bonus        # more sources = higher confidence
           - outlier_penalty            # one source disagrees = penalty
           - staleness_penalty          # older data = lower confidence
           - historical_reliability     # provider's 24h reliability score
```

**Downstream usage**:
- Intelligence agents can choose to ignore data with confidence < 0.5
- Decision agents weight signals by their source confidence
- Report Generator includes a "Data Quality" section showing average confidence per section
- Dashboard shows confidence badges on every panel

---

## 8. What changes from STEP 3 to STEP 3.5

| Aspect | STEP 3 | STEP 3.5 |
|---|---|---|
| Layering | Loose — agents could call providers directly | Strict — nothing above Layer 1 calls providers, nothing above Layer 3 touches raw data |
| Databases | 4 schemas (raw, processed, AI, historical) | 12 schemas (10 institutional + 2 infra) |
| Market Replay | Not present | New — minute-by-minute cross-domain snapshots |
| AI Memory | Not present | New — predictions + outcomes + lessons learned |
| Providers | 7 (5 market + 2 macro) | 14 (6 market + 2 macro + 4 news + 1 filings + 1 prediction markets + 1 dev) |
| Agent organization | Flat under Supervisor (78 agents) | Hierarchical: 10 divisions × 55 teams (166 agents total) |
| Confidence scoring | Implicit in event metadata | Explicit column on every database row |
| News sources | Generic news-agent | 4 dedicated news providers (Reuters, CNN, WSJ, CNBC) |
| Macro sources | FRED only | FRED + Trading Economics + 8 specialized macro teams |
| Forecast models | 1 ensemble agent | 6 dedicated model teams (ARIMA, LSTM, Transformer, XGBoost, TabPFN, Ensemble) |
| Reporting | 1 Report Engine module | 5 reporting teams (Live, Daily, Weekly, Intraday, Alert) |
| Self-Validation | 1 self-correction agent | 4 teams (Audit, Accuracy, Comparison, Correction) |

---

## 9. Implementation plan

STEP 3.5 regenerates three directories in the existing monorepo:

1. `providers/` — adds 8 new provider adapters
2. `agents/` — restructures into 10 hierarchical divisions with team leaders
3. `database/` — adds 8 new schemas (Options, News, Macro, Validation, AI Memory, Market Replay + split existing)

Plus updates:
- `providers/failover.yaml` — adds Databento as institutional-grade source
- `database/migrations/` — new migration for the schema split
- `docs/architecture/STEP-3.5-ARCHITECTURE.md` — this document
- Top-level `README.md` — references the new layering

**No changes** to:
- `apps/` (Next.js + FastAPI scaffolds unchanged)
- `engines/` (7 engines unchanged)
- `runtime/` (8 modules unchanged)
- `packages/` (5 packages unchanged)
- `schemas/events/` (event taxonomy unchanged — divisions are an organizational concept)
- `plugins/` (26 plugins unchanged)
- `.github/`, `scripts/`, `tools/`, `configs/`, `infrastructure/` (unchanged)

---

## 10. Approval gate

This document is the authoritative architectural reference going forward.
STEP 4 implementation will follow the 8-layer strict hierarchy.

Proceeding to regenerate `providers/`, `agents/`, and `database/` per this spec.
