# STEP 2.1 — Architecture Revisions (User-Approved, 20 Changes)

This document reflects the 20 changes the user approved on top of STEP 2.
It is the authoritative architectural reference for STEP 3 (skeleton) and STEP 4 (implementation).

---

## Change 1 — Dedicated Data Collection Layer (Highest Priority)

The pipeline before any analysis:

```
Data Collection AI → Data Validation AI → Data → Standardization AI → Market Data Database → Analysis Agents
```

Responsibilities:
- Real-time collection
- Timestamp normalization
- Duplicate removal
- Missing data detection
- Data quality scoring
- Cross-provider validation
- Provider failover
- Historical recording

**Rule**: nothing enters the system without passing through this pipeline.

**Implementation**: 3 dedicated agents under `agents/data-collection/`:
- `collection-agent` — pulls from providers, normalizes timestamps
- `validation-agent` — deduplication, missing-data detection, quality scoring, cross-provider validation
- `standardization-agent` — canonical schema mapping, unit normalization

The Market Data Database (Change 14) only accepts writes from `standardization-agent`. All other agents read from it.

---

## Change 2 — Split AI into Two Levels

- **Raw Intelligence** produces facts (e.g., "RSI = 40.3", "IV rank = 67", "News sentiment = +0.42").
- **Decision Intelligence** produces conclusions (e.g., "Market regime is trending", "Bull scenario probability = 62%").

**Rule**: never mix them. Raw agents never emit decisions. Decision agents never emit raw facts.

**Implementation**: two top-level directories under `agents/`:
- `agents/raw-intelligence/` — TA (23 agents), Options (15), News, Macro, Cross-Market (20)
- `agents/decision-intelligence/` — Market Regime, Timeframe Sync, Forecast, Scenario, Volatility, Expected Move, Probability Tree, AI Consensus, Probability Engine

---

## Change 3 — Supervisor AI

Every AI agent reports to a Supervisor. Located at `agents/supervisor/`.

Responsibilities:
- Detect conflicting signals (e.g., TA bullish + News bearish on same symbol)
- Check stale data (last update > threshold per asset class)
- Detect failing agents (no heartbeat in N seconds)
- Trigger retries (with backoff, max 3)
- Confidence weighting (per-agent trust score, dynamically adjusted)
- Report generation (delegates to Report Engine)
- Self-learning (adjusts agent weights based on outcomes)
- Performance statistics (per-agent throughput, accuracy, latency)

**Implementation**: `agents/supervisor/supervisor-agent.py` subscribes to ALL events, maintains a registry of agent health + trust scores, publishes `supervisor:conflict-detected`, `supervisor:agent-failing`, `supervisor:retry-requested`, `supervisor:confidence-adjusted`.

---

## Change 4 — Institutional Validation Layer

Before any report reaches the dashboard, it passes through this layer at `agents/validator/`.

Validation criteria (all must pass):
- **Confidence** — overall confidence score ≥ threshold (configurable, default 0.65)
- **Evidence** — minimum number of supporting data points (default: 5)
- **Data freshness** — all source data updated within last N seconds (default: 60s for live, 1d for macro)
- **Source count** — at least M independent sources agree (default: 2)
- **Agreement score** — weighted agreement across agents ≥ threshold (default: 0.70)

**Implementation**: `agents/validator/validation-agent.py` subscribes to `report:generation-completed`, runs the 5 checks, publishes `validator:report-approved` or `validator:report-rejected` with detailed reasoning.

---

## Change 5 — Replace "Forecast Module" with "Market Intelligence"

The Forecast Module is now one component of a broader **Market Intelligence** module.

Market Intelligence contains:
- Forecast (the original)
- Scenario Analysis (Bull / Base / Bear)
- Regime Detection (from Decision Intelligence)
- Volatility Projection
- Expected Move
- Probability Tree
- AI Consensus (aggregate across all models)

**Implementation**: `agents/decision-intelligence/` houses all 7 sub-agents. The frontend module `modules/market-intelligence/` displays their combined output.

---

## Change 6 — Expand Technical Analysis Module (23 AI agents, plugin-based)

Each indicator is an **independent plugin** under `plugins/indicators/` or `plugins/patterns/`. Each agent under `agents/raw-intelligence/technical-analysis/` consumes one or more plugins and emits signals.

```
agents/raw-intelligence/technical-analysis/
├── multi-timeframe/      ├── volume-profile/
├── trend/                ├── volume-price/
├── candlestick/          ├── support-resistance/
├── ema/                  ├── liquidity/
├── sma/                  ├── smart-money/
├── vwap/                 ├── escape-top/
├── rsi/                  ├── entry/
├── macd/                 └── pull-up-pattern/
├── adx/
├── atr/
├── bollinger/
├── fibonacci/
├── elliott-wave/
├── wyckoff/
├── chan-theory/
```

Each agent ships with: `README.md`, `manifest.py`, `config.py`, `types.py`, `agent.py`. The `agent.py` class is a skeleton in STEP 3; logic comes in STEP 4.

---

## Change 7 — Expand Options Module (15 AI agents)

```
agents/raw-intelligence/options/
├── greeks/               ├── max-pain/
├── iv/                   ├── open-interest/
├── iv-crush/             ├── 0dte/
├── iv-rank/              ├── volatility-surface/
├── skew/                 ├── expected-move/
├── option-flow/          └── probability-of-profit/
├── dealer-position/
├── gamma-exposure/
├── gamma-flip/
```

Plugin counterparts live under `plugins/options/`.

---

## Change 8 — Cross-Market Layer

Dedicated agents for 20 instruments/markets that feed SPY Intelligence:

```
agents/raw-intelligence/cross-market/
├── spy/    ├── vix/    ├── gold/
├── spx/    ├── vvix/   ├── oil/
├── es/     ├── move/   ├── copper/
├── qqq/    ├── dxy/    ├── usdjpy/
├── nq/     ├── tnx/    ├── europe/
├── iwm/    ├── asia/
├── dia/    ├── crypto/
├── soxx/
```

Each agent emits `cross-market:<symbol>-state` events. A `cross-market-spy-intelligence` aggregator subscribes to all and emits `cross-market:spy-intelligence-updated`.

---

## Change 9 — Market Regime AI

Every decision begins with regime classification. Located at `agents/decision-intelligence/market-regime/`.

Regimes:
- Trending
- Ranging
- Breakout
- Mean Reversion
- High Vol
- Low Vol
- News Driven
- Option Driven
- Dealer Controlled

**Rule**: no indicator is interpreted without regime context. Every Raw Intelligence signal is enriched by the current regime before Decision Intelligence consumes it.

**Implementation**: `market-regime-agent` subscribes to all raw-intelligence events + market data, emits `decision:regime-classified` with `{ symbol, regime, confidence, evidence }`. Other decision agents subscribe to this as a prerequisite input.

---

## Change 10 — Timeframe Synchronization AI

Located at `agents/decision-intelligence/timeframe-sync/`.

```
Monthly → Weekly → Daily → 4H → 1H → 30M → 15M → 5M → 1M → Alignment Score
```

The agent computes a per-symbol alignment score (0–100) indicating how aligned the trend is across all 9 timeframes. Emits `decision:timeframe-alignment-updated`.

---

## Change 11 — Upgrade Event Bus

Every event MUST contain these 8 metadata fields:

```typescript
interface BusEvent<T = unknown> {
  eventId:        string;        // UUID
  eventType:      string;        // e.g., "market:quote-updated"
  timestamp:      string;        // ISO 8601 UTC
  provider:       string;        // source provider/agent
  latency:        number;        // ms from source to bus publish
  confidence:     number;        // 0..1
  dataVersion:    string;        // semver of the payload schema
  retryCount:     number;        // 0 on first publish
  agentId:        string;        // emitting agent ID
  processingTime: number;        // ms the agent spent producing this
  payload:        T;             // event-specific
}
```

The bus rejects any event missing these fields. Enforced by schema validation at the bus boundary.

---

## Change 12 — AI Self-Correction Engine

Located at `agents/self-correction/`.

Pipeline:
```
Prediction → Market Outcome → Compare → Error → Weight Adjustment → Improve Model
```

Every prediction is scored. The engine maintains a per-model weight table that the Supervisor uses for confidence weighting (Change 3) and the Forecast Ensemble uses for composition (Change 5).

**Implementation**: `self-correction-agent` subscribes to `forecast:trajectory-computed` and `market:quote-updated` (delayed), compares predicted vs actual, publishes `learning:prediction-scored` and `learning:weight-adjusted`.

---

## Change 13 — Modular Plugin Architecture

Every indicator becomes installable. Plugins live under `plugins/`:

```
plugins/
├── indicators/    # TA computation plugins (EMA, RSI, VWAP, MACD, ADX, ATR, Bollinger, Fibonacci, Stochastic, CCI, Williams-R, ...)
├── options/       # options computation plugins (Greeks, IV, Skew, Gamma Exposure, Max Pain, ...)
├── patterns/      # pattern recognition plugins (Candlestick, Elliott Wave, Wyckoff, Chan Theory, Volume Profile, ...)
└── dark-pool/     # alternative data plugins (future)
```

Each plugin is a self-contained package with: `manifest.ts` (or `.py`), `plugin.ts` (the computation), `types.ts`, `tests/`, `README.md`. Plugins are loaded by `engines/plugin-engine/` at startup.

A `tools/plugin-scaffolder/` CLI generates new plugin boilerplate.

---

## Change 14 — Database Separation

Four logical databases (implemented as Postgres schemas in a single Supabase instance, or physically separate clusters in production):

| Database | Purpose | Writer |
|---|---|---|
| `raw_market_data` | Untouched provider output | `collection-agent` only |
| `processed_market_data` | Normalized, deduplicated, validated | `standardization-agent` only |
| `ai_intelligence` | Agent outputs, predictions, signals, weights | All agents (their own tables) |
| `historical_reports` | Generated reports + backtests | `report-engine`, `validator-engine` |

**Rule**: never mix raw and processed data. Reader access is open to authenticated agents; writer access is locked to the designated agent per database.

---

## Change 15 — Dashboard Should Never Calculate

The Next.js dashboard does ONLY:
- Display
- Filter
- Search
- Layout
- User interaction

NO market calculations. NO AI. NO indicators. NO forecasting. All numbers arrive via events or API responses from the Python backend.

**Implementation**: ESLint rule `no-calc-in-dashboard` bans `Math.*`, `*`, `/`, `+`, `-` (except in approved utility files). Dashboard components only consume TanStack Query results and bus subscriptions.

---

## Change 16 — Future Automation Layer

Architecture reserves space for:

```
Execution AI → Risk AI → Position AI → Broker API
```

Located at `agents/automation/`:
- `execution/` — order placement
- `risk/` — pre-trade risk checks
- `position/` — position management
- `broker/` — broker API adapter (IBKR, Alpaca, etc.)

**Status**: skeleton only in STEP 3. Disabled by feature flag. No execution logic.

---

## Change 17 — Agent Health Dashboard

Every AI agent exposes:

| Metric | Type |
|---|---|
| `running` | boolean |
| `last_update` | timestamp |
| `cpu` | percent |
| `memory` | MB |
| `api_latency` | ms |
| `queue_length` | int |
| `error_count` | int (since start) |
| `restart_count` | int |
| `confidence` | 0..1 (current trust score) |
| `version` | semver |

**Implementation**: `runtime/health-monitor/` aggregates metrics from all agents via heartbeat events. Dashboard module `modules/agent-health/` displays them.

---

## Change 18 — Data Quality Dashboard

Every provider exposes:

| Metric | Type |
|---|---|
| `connection` | `connected` / `disconnected` / `degraded` |
| `delay` | ms (last response time) |
| `missing_bars` | int (count in last 24h) |
| `missing_ticks` | int |
| `api_errors` | int (last 24h) |
| `failover_count` | int (last 24h) |
| `freshness` | ms (age of most recent data) |
| `reliability_score` | 0..1 (rolling 24h) |

**Implementation**: `runtime/health-monitor/` tracks per-provider metrics. Dashboard module `modules/data-quality/` displays them.

---

## Change 19 — Expanded Monorepo

Monorepo now contains these top-level directories:

```
athena-x/
├── apps/           packages/      agents/        engines/
├── plugins/        providers/     schemas/       database/
├── runtime/        docs/          tests/         scripts/
├── tools/          configs/       .github/
```

Each has a clear purpose documented in its README.

---

## Change 20 — Module Implementation Order (Revised)

The STEP 4 implementation order is now:

1. Foundation / Core Runtime
2. Data Collection AI
3. Data Validation AI
4. Database Layer
5. Event Bus
6. Technical Analysis Engine
7. Options Intelligence
8. Market Intelligence (Macro + News + Sentiment)
9. Cross-Market Intelligence
10. AI Forecast Engine
11. Probability Engine
12. Supervisor AI
13. Validation AI (Institutional Validation Layer)
14. Report Engine
15. Dashboard / UI
16. Self-Correction & Learning
17. Backtesting & Strategy Validation
18. Performance Optimization

Each step ships with `tsc --noEmit` + `next lint` + `pytest` + `next build` passing. Zero errors before proceeding to the next.

---

## Summary of Architectural Impact

These 20 changes transform STEP 2's design from "modular monolith with agents" into a **strictly layered, plugin-based, supervisor-governed, continuously-learning intelligence platform**.

Key new architectural elements that STEP 3 must scaffold:
- 3 data-collection agents (Change 1)
- 23 TA agents + matching indicator plugins (Change 6, 13)
- 15 options agents + matching options plugins (Change 7, 13)
- 20 cross-market agents (Change 8)
- 9 decision-intelligence agents (Changes 5, 9, 10)
- 1 supervisor agent (Change 3)
- 1 validation agent (Change 4)
- 1 self-correction agent (Change 12)
- 4 reserved automation agents (Change 16)
- 7 engines (data, AI runtime, ONNX, backtest, report, plugin, learning)
- 4 logical databases (Change 14)
- Enhanced event schema with 8 mandatory metadata fields (Change 11)
- Plugin architecture with scaffolding tool (Change 13)
- Health + data-quality dashboards (Changes 17, 18)
- No-calc-in-dashboard ESLint rule (Change 15)

**Total agents**: 77 (3 + 23 + 15 + 20 + 2 news/macro + 9 + 1 + 1 + 1 + 4 - 1 forecast already counted = 78, with cross-market spy-intelligence aggregator = 79)
**Total plugins**: ~26 (14 indicators + 6 options + 6 patterns)
**Total providers**: 7 (Yahoo, Finnhub, Polygon, FlashAlpha, FRED, AlphaVantage, Simulated-dev-only)

Proceeding to STEP 3: generate the complete monorepo skeleton.
