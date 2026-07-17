# STEP 4 — Implementation Plan (Approved with Modifications)

> **Objective**: Build an institutional-grade AI trading research platform where
> **data accuracy is the highest priority**.
>
> **Goal**: Produce a 1-minute institutional trading report.
>
> **Mandatory rule**: The dashboard never performs calculations; it only consumes
> validated outputs from backend services. This architecture is the **required
> baseline** for all future development.

---

## 0. Approval Status

**Approved with modifications** by the user. The user's verbatim directive:

> "Approved with modifications. Before implementing intelligence or UI, prioritize
> building a production-grade data platform. The order should be: Foundation →
> Data Collection → Validation → Standardization → Database → Event Bus →
> Technical Analysis → Options Intelligence → Cross-Market → News & Macro →
> Forecast → Decision Intelligence → Supervisor → Self-Validation → Reporting →
> Dashboard → Backtesting → Performance. Every stage must pass functional,
> integration, data accuracy, stress, failover, and performance tests before
> proceeding to the next stage. The dashboard must never perform calculations;
> it only consumes validated outputs from backend services. This architecture is
> the required baseline for all future development."

---

## 1. The 18 Stages (in strict dependency order)

| Stage | Name | Layer | Depends on |
|---|---|---|---|
| 1 | Core Foundation | infra | — |
| 2 | Data Collection AI ⭐ | Layer 1 | Stage 1 |
| 3 | Validation AI ⭐⭐⭐ | Layer 2 | Stage 2 |
| 4 | Data Standardization | Layer 3 | Stage 3 |
| 5 | Database Layer | Layer 4 | Stage 4 |
| 6 | Event Bus | cross-cutting | Stages 1–5 |
| 7 | Technical Analysis Engine | Layer 5 | Stage 6 |
| 8 | Options Intelligence | Layer 5 | Stage 6 |
| 9 | Cross-Market Intelligence | Layer 5 | Stage 6 |
| 10 | News & Macro Intelligence | Layer 5 | Stage 6 |
| 11 | Forecast Engine | Layer 5 | Stages 7–10 |
| 12 | Decision Intelligence | Layer 6 | Stage 11 |
| 13 | Supervisor AI | supervisor | Stage 12 |
| 14 | Self-Validation | Layer 5 (validation) | Stages 11, 12 |
| 15 | Reporting Engine | Layer 7 | Stage 12 |
| 16 | Dashboard | Layer 8 | Stage 15 |
| 17 | Backtesting | replay | Stages 5, 7–12 |
| 18 | Performance & Optimization | cross-cutting | All |

---

## 2. Per-Stage Specifications

### Stage 1 — Core Foundation ✅

**Components**:
- Event Bus (typed pub/sub, 10 mandatory metadata fields)
- Configuration (pydantic-settings, env vars, YAML)
- Logger (structlog, structured JSON, correlation IDs)
- Health Monitor (heartbeats, agent health tracking)
- Scheduler (APScheduler for cron + on-demand tasks)
- Dependency Injection (lightweight container)
- Authentication (Supabase JWT verification)
- Secrets Management (env vars + optional Vault integration)

**Exit criteria**:
- ✅ All services communicate (event bus publish/subscribe works end-to-end)
- ✅ Heartbeats and health checks work (every agent emits `system:agent-heartbeat`)
- ✅ Structured logging is operational (JSON logs with correlation IDs)

**Acceptance tests** (see §3):
- Functional: each component unit-tested in isolation
- Integration: components wired together via DI container
- Data accuracy: N/A (no data flowing yet)
- Stress: 10,000 events/sec sustained for 60s on the bus
- Failover: bus reconnects after Redis restart
- Performance: <1ms publish latency p99

---

### Stage 2 — Data Collection AI ⭐ (Highest Priority)

**Goal**: Implement ONLY data collection. No calculations.

**Adapters to build** (20 instruments × multiple providers + alt data):

Market data collectors (20 instruments):
- ES, SPY, SPX, QQQ, NQ, IWM, DIA, SOXX
- VIX, VVIX, MOVE, TNX, DXY
- Gold, Oil, Copper, USDJPY
- Europe, Asia, Crypto

News collectors:
- Reuters, CNBC, WSJ, CNN

Macro collectors:
- Economic Calendar
- Earnings calendar
- Federal Reserve (FOMC, funds rate, balance sheet)
- Treasury yields

Alternative data collectors:
- Polymarket (prediction markets)
- Fear & Greed Index (CNN)
- Dark Pool prints
- Option Flow
- Gamma exposure
- Open Interest

**Exit criteria**:
- All collectors download data from their respective providers
- Raw payloads land in `raw_landing` schema
- Provider failover chain works (Yahoo → Finnhub → Polygon → ...)
- Every payload includes provenance (provider, received_at, ingest_id)

**Acceptance tests**:
- Functional: each adapter fetches its data type correctly
- Integration: collectors emit `market:quote-updated` etc. on the bus
- Data accuracy: cross-check fetched data against provider's web UI
- Stress: 1000 symbols × 5 providers = 5000 concurrent fetches
- Failover: simulate Yahoo outage → automatic switch to Finnhub
- Performance: <500ms per quote fetch

---

### Stage 3 — Validation AI ⭐⭐⭐

**Goal**: Before storing ANY data, validate it.

**Validation logic**:
- Cross-provider verification (Yahoo says 752.44, Polygon 752.46, Finnhub 752.45 → tolerance < 0.02 → Verified)
- Timestamp validation (reject out-of-order events)
- Missing data detection (gaps in bar sequences)
- Duplicate detection (same payload from multiple sources)
- Outlier rejection (one source says 742 when others say 752 → REJECT)
- Confidence scoring (0.0–1.0 per data point)
- Failover logic (trigger provider switch on validation failure)

**Rule**: Nothing reaches the Layer 4 databases until validated.

**Exit criteria**:
- 5 validator agents operational (price, volume, options, news, time)
- Every validated payload carries a `confidence` score
- Outlier rejection tested with synthetic bad data
- Failover triggers when validation fails repeatedly

**Acceptance tests**:
- Functional: each validator correctly verifies/rejects test data
- Integration: validator sits between collectors and standardizers
- Data accuracy: validated data matches provider consensus
- Stress: 10,000 events/sec through validation pipeline
- Failover: provider rejection triggers automatic failover
- Performance: <2ms validation latency per event

---

### Stage 4 — Data Standardization

**Goal**: Convert every provider's idiosyncratic schema into one canonical format.

**Normalization targets**:
- Symbols: `BRK.B`, `BRK-B` → `BRK.B`
- Time zones: local → UTC ISO 8601
- Units: cents → dollars, % → decimal
- Field names: `close`, `Close`, `last`, `price` → `last_price`
- Precision: per asset class (e.g., equity 4 decimals, FX 6 decimals)
- Market calendars: NYSE, CME, FX, crypto (24/7)

**Exit criteria**:
- 4 standardization agents operational (market, options, news, macro)
- Canonical schemas enforced via Pydantic models
- Each standardizer is the ONLY writer to its database

---

### Stage 5 — Database Layer

**Goal**: 12 separate Postgres schemas, each with one designated writer.

**Schemas** (per STEP 3.5):
- `raw_landing` — Layer 1 raw payloads
- `market_db` — validated + standardized market data
- `options_db` — validated + standardized options data
- `news_db` — validated + standardized news
- `macro_db` — validated + standardized macro
- `validation_db` — validation decisions + quality scores
- `ai_db` — intelligence agent outputs
- `forecast_db` — decision agent outputs
- `historical_db` — reports + backtests
- `market_replay_db` — minute-by-minute cross-domain snapshots
- `ai_memory_db` — predictions + outcomes + lessons
- `app` — user workspaces, watchlists, module instances

**Exit criteria**:
- All 12 schemas created with proper indexes
- RLS policies enforced (writer-locked per schema)
- Migrations applied via Supabase
- Backup/restore tested

---

### Stage 6 — Event Bus

**Goal**: Connect everything: Provider → Validation → Database → AI Agents → Dashboard.

**Components**:
- Backend bus (Redis Pub/Sub + NATS JetStream for queue semantics)
- WebSocket bridge (mirrors backend events to frontend)
- Frontend bus mirror (in-process pub/sub in the browser)
- Event schema validation (rejects events missing mandatory metadata)
- Backpressure handling (drop stale market data >500ms)

**Exit criteria**:
- End-to-end event flow: provider → bus → standardizer → DB → bus → dashboard
- All 10 mandatory metadata fields enforced on every event
- WebSocket bridge handles 10,000 concurrent connections
- Frontend bus delivers events to subscribed components

---

### Stages 7–10 — Intelligence Agents

**Stage 7 — Technical Analysis Engine** (23 plugins + 23 agents):
- Multi-timeframe, Trend, Candlestick, EMA, SMA, VWAP, RSI, MACD, ADX, ATR,
  Bollinger, Fibonacci, Elliott Wave, Wyckoff, Chan Theory (缠论),
  Volume Profile, Volume-Price Analysis (量价), Smart Money, Liquidity,
  Escape Top (逃顶), Entry (进场), Pull-Up Pattern (拉升), Support/Resistance

**Stage 8 — Options Intelligence** (15 agents):
- Greeks, IV, IV Rank, IV Percentile, IV Crush Probability,
  Gamma Exposure, Gamma Flip, Dealer Positioning, Open Interest,
  Option Flow, 0DTE Analysis, Max Pain, Volatility Surface, Expected Move,
  Probability of Profit

**Stage 9 — Cross-Market Intelligence**:
- Correlate ES, SPY, SPX, NQ, QQQ, SOXX, VIX, Bonds, Dollar, Oil, Gold,
  Europe, Asia, Crypto

**Stage 10 — News & Macro Intelligence**:
- Reuters, CNBC, WSJ, CNN
- Federal Reserve, Treasury, Economic Calendar, Earnings, Geopolitics

**Exit criteria per stage**:
- All agents read from Layer 4 databases only (never call providers)
- All agents write to `ai_db` (each owns its own tables)
- All agents emit `system:agent-heartbeat` every 5s
- Supervisor can detect agent failures

---

### Stage 11 — Forecast Engine

**Models**:
- ARIMA (statistical, CPU)
- LSTM (PyTorch GPU — NEVER browser)
- Transformer (PyTorch GPU — NEVER browser)
- XGBoost (GPU)
- LightGBM (small → browser ONNX, large → GPU)
- CatBoost (GPU)
- TabPFN (GPU)
- Ensemble (combines all using dynamic weights from Stage 14)

**Exit criteria**:
- All models loadable and inferable
- Routing table enforced (LSTM/Transformer never in browser)
- Inference latency: browser ONNX <50ms, Python GPU <500ms
- Model registry operational

---

### Stage 12 — Decision Intelligence

**Agents**:
- Market Regime (trending/ranging/breakout/mean-reversion/high-vol/low-vol/news-driven/option-driven/dealer-controlled)
- Trend Day Probability
- Reversal Probability
- Trade Timing
- Option Timing
- IV Crush Risk
- Probability Tree
- AI Consensus

**Rule**: Decision agents ONLY combine information. NO calculations.

---

### Stage 13 — Supervisor AI

**Monitors**:
- Agent health (heartbeats, restart counts, error rates)
- Data quality (validation_db quality_scores)
- Conflicts (bullish TA + bearish News on same symbol)
- Confidence (per-agent trust scores, dynamically adjusted)
- Recovery (trigger retries with exponential backoff, max 3)

---

### Stage 14 — Self-Validation

**Compares**:
- Prediction vs outcome (forecast.trajectory-computed vs actual market:bar-closed)
- Model accuracy (per model, per regime, per horizon)
- Indicator accuracy (which indicators predicted direction correctly)
- Decision accuracy (which decisions produced profitable signals)

**Auto-adjusts**:
- Model weights in `ai_db.model_weights`
- Lessons in `ai_memory_db.lessons`
- Insights in `ai_memory_db.insights`

---

### Stage 15 — Reporting Engine

**Generates**:
- 1-minute report (ultra-fast, key signals only)
- 5-minute report (slightly deeper)
- Intraday report (15-min snapshots during market hours)
- Weekly report (comprehensive, deep analysis)
- PDF (institutional dark theme)
- Markdown (canonical)
- Dashboard summaries (compact JSON for dashboard rendering)

---

### Stage 16 — Dashboard

**Only now** build the live dashboard.

**Rule**: It is a presentation layer that **never performs calculations**.
It only consumes validated outputs from backend services via:
- TanStack Query (for request-response)
- WebSocket subscriptions (for real-time updates)
- Supabase Realtime (for database changes)

**Modules** (12):
- Dashboard, Live Market Data, Technical Analysis, News Intelligence,
  Options Intelligence, Macro Intelligence, Market Intelligence,
  Probability Engine, Report Generator, Self Validation,
  Agent Health Dashboard, Data Quality Dashboard

---

### Stage 17 — Backtesting

**Replay** historical sessions using the same pipeline to:
- Evaluate strategies (ATHENA-X Ensemble, TA-only, News-only, Options-only, Macro-only, Forecast-only)
- Validate predictions (compare Stage 11 forecasts to actual outcomes)
- Train AI models (supervised learning on labeled historical windows)
- Debug decisions ("what did the AI know at 10:15:32 on 2026-03-14?")

**Implementation**: `engines/backtest-engine/` using `vectorbt`. Real backtests, never mock.

---

### Stage 18 — Performance & Optimization

**Optimize**:
- GPU usage (model batching, warmup, memory pooling)
- Caching (Redis cache layer, TanStack Query stale times)
- Database indexes (per-query analysis)
- WebSocket throughput (compression, multiplexing)
- Memory usage (object pooling, garbage collection tuning)
- Latency (end-to-end p99 < 100ms for live data)
- Parallel execution (asyncio task pools, ProcessPoolExecutor for CPU-bound)

---

## 3. Mandatory Acceptance Criteria (every stage)

A stage is **only considered complete** when ALL six test categories pass:

### 3.1 Functional tests
- All features behave as specified
- Every component has unit tests
- Every public API has contract tests
- Coverage ≥80% on services/business logic

### 3.2 Integration tests
- Downstream components continue to function correctly
- End-to-end flows work (e.g., provider → bus → standardizer → DB)
- No regressions in already-passing stages

### 3.3 Data accuracy tests
- Cross-checked against provider data
- Sampled data points manually verified
- Statistical comparison (mean, stddev, correlation) against reference

### 3.4 Stress tests
- Simulate high event rates (e.g., FOMC, CPI releases)
- 10× expected peak load for 60s sustained
- No data loss, no crashes, no unbounded latency growth

### 3.5 Recovery tests (failover)
- Confirm failover works when providers disconnect
- Simulate Redis/NATS/Postgres restart
- Simulate agent crash + supervisor restart
- Zero data loss, automatic recovery <30s

### 3.6 Performance tests
- Measure latency (p50, p95, p99)
- Measure throughput (events/sec)
- Measure resource usage (CPU, memory, GPU)
- Latency budgets per stage (see §4)

---

## 4. Performance Budgets per Stage

| Stage | Component | p50 latency | p99 latency | Throughput |
|---|---|---|---|---|
| 1 | Event bus publish | <1ms | <5ms | 10,000 events/sec |
| 1 | Logger write | <0.5ms | <2ms | 50,000 logs/sec |
| 2 | Quote fetch | <200ms | <500ms | 1000 symbols/sec |
| 3 | Validation | <1ms | <2ms | 10,000 events/sec |
| 4 | Standardization | <0.5ms | <1ms | 20,000 events/sec |
| 5 | DB write | <5ms | <20ms | 5000 writes/sec |
| 6 | WebSocket bridge | <10ms | <50ms | 10,000 clients |
| 7 | TA indicator (per bar) | <5ms | <20ms | 1000 bars/sec |
| 8 | Greeks computation | <10ms | <50ms | 500 options/sec |
| 11 | Browser ONNX inference | <30ms | <50ms | 100 inferences/sec |
| 11 | Python GPU inference (LSTM) | <200ms | <500ms | 50 inferences/sec |
| 15 | 1-minute report generation | <2s | <5s | 1 report/min |
| 16 | Dashboard initial load | <1s | <3s | — |
| 16 | Dashboard live update (via WS) | <100ms | <500ms | — |

---

## 5. Quality Gates (per stage)

Every stage ships with these gates passing:

```bash
# Python
uv run ruff check .
uv run mypy .
uv run pytest --cov=src --cov-report=term-missing --cov-fail-under=80
uv run pytest tests/ -m "functional"     # all functional tests pass
uv run pytest tests/ -m "integration"    # all integration tests pass
uv run pytest tests/ -m "accuracy"       # all data accuracy tests pass
uv run pytest tests/ -m "stress"         # all stress tests pass
uv run pytest tests/ -m "failover"       # all recovery/failover tests pass
uv run pytest tests/ -m "performance"    # all performance tests pass

# TypeScript
pnpm --filter @athena-x/dashboard typecheck
pnpm --filter @athena-x/dashboard lint
pnpm --filter @athena-x/dashboard test
pnpm --filter @athena-x/dashboard build
```

**Zero errors allowed.** Any failing gate blocks progression to the next stage.

---

## 6. Stage 1 Implementation Plan (Starting Now)

Stage 1 deliverables, in implementation order:

### 6.1 Configuration (`runtime/config/`)
- Pydantic Settings class loading from env vars + YAML
- Per-environment configs (dev/staging/production)
- Validation at startup (fail fast on missing required vars)
- Secrets management (env vars first, optional HashiCorp Vault integration)

### 6.2 Logger (`runtime/logger/`)
- structlog with JSON output
- Correlation IDs (per request, per event)
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Async-safe, thread-safe
- Optional log shipping to backend `/logs` endpoint

### 6.3 Event Bus (`runtime/event-bus/`)
- Redis Pub/Sub transport
- NATS JetStream transport (for queue semantics)
- 10 mandatory metadata fields enforced via Pydantic
- Pattern-based subscriptions (e.g., `market:*`)
- Backpressure handling (drop stale market data >500ms)
- Bus client with connect/reconnect logic

### 6.4 Health Monitor (`runtime/health-monitor/`)
- AgentHealth + ProviderHealth types (already scaffolded in STEP 3)
- HealthRegistry: tracks all registered agents
- Heartbeat aggregator: listens to `system:agent-heartbeat` events
- Health check endpoint: `/health/agents`, `/health/providers`
- Alerting: emits `supervisor:agent-failing` when agent misses 3 heartbeats

### 6.5 Scheduler (`runtime/scheduler/`)
- APScheduler wrapper
- Cron-style schedules (e.g., every weekday 09:30 ET)
- On-demand task submission
- Persistent job store (Redis-backed)
- Failure handling + retry

### 6.6 Dependency Injection (`runtime/di/`)
- Lightweight DI container (no external deps)
- Token-based injection
- Singleton + factory scopes
- Used to wire all Stage 1 components together

### 6.7 Authentication (`runtime/auth/`)
- Supabase JWT verification
- FastAPI dependency for protected routes
- Service-role key for backend agents (bypasses RLS)
- Token refresh handling

### 6.8 Secrets Management (`runtime/secrets/`)
- env vars (primary)
- `.env` file (dev only)
- Optional Vault integration (production)
- Secret rotation helpers

### 6.9 Integration
- DI container wires all components
- FastAPI lifespan starts/stops everything
- Health endpoints expose status
- Smoke test: emit a test event, see it arrive at subscriber

### 6.10 Acceptance Tests
- Functional: unit tests for each component
- Integration: DI container wires everything, end-to-end event flow
- Stress: 10,000 events/sec for 60s
- Failover: kill Redis, verify reconnect
- Performance: <1ms publish latency p99

---

## 7. Approval Gate

This plan is the **required baseline** for all future development.

**Proceeding now with Stage 1 implementation.**
