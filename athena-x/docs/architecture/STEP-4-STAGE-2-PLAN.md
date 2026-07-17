# STEP 4 — Stage 2 Plan (Enhanced, User-Approved)

> **Status**: Approved with enhancements.
> **Stage 1 status**: ✅ Complete (78/78 tests pass).
> **Stage 2 purpose**: Build a production-grade data collection layer. **Nothing calculates**.

---

## 0. Approval Gate

User's verbatim directive:

> "I would approve Stage 2 with several important additions. Since this stage is
> the foundation of your entire platform, it's worth making it as robust as possible."

The 10 enhancements (institutional metadata, raw archival, provider health,
session awareness, data freshness, etc.) are non-negotiable requirements.

---

## 1. The 10 Enhanced Requirements

### 1.1 Market Data Collectors (20 instruments)

**Primary Markets (8)**: ES (main), SPY, SPX, NQ, QQQ, DIA, IWM, SOXX

**Volatility (3)**: VIX, VVIX, MOVE

**Rates & FX (3)**: TNX (10Y Treasury), DXY, USDJPY

**Commodities (3)**: Gold, Oil, Copper

**Global Markets (3)**: Europe indices, Asia indices, Crypto (BTC, ETH)

Each collector:
- Polls at the instrument's natural frequency (e.g., ES every 1s, VIX every 15s)
- Fails over across the provider chain
- Emits `market:quote-updated` and `market:bar-closed` events
- Writes raw payload to `raw_landing/`
- Computes nothing — just downloads and forwards

### 1.2 Options Data Collectors (16 metrics)

Separate collection service for:
- Option chain
- Open Interest
- Volume
- Greeks
- IV
- IV Rank (raw data only — computation in Stage 8)
- IV Percentile (raw data only)
- Gamma Exposure (raw data only)
- Gamma Flip (raw data only)
- Dealer Positioning (raw data only)
- Max Pain (raw data only)
- Expected Move (raw data only)
- 0DTE data
- Option Flow
- Dark Pool
- Short Interest (if available)

**Rule**: Even metrics that require later computation (IV Rank, GEX, Max Pain,
Expected Move) — the **raw data required to derive them** is collected now.

### 1.3 News Collection (14 sources, split by category)

| Category | Sources |
|---|---|
| Wire services | Reuters, Bloomberg (if licensing permits) |
| Financial media | CNBC, WSJ, CNN Business |
| Regulatory | SEC Filings |
| Government | Federal Reserve, Treasury |
| Calendars | Economic Calendar, Earnings Calendar |
| Company news | MAG7 (NVDA, AAPL, MSFT, GOOGL, AMZN, META, TSLA) |
| Thematic | Geopolitical, Energy, Semiconductor |

**Per-article schema** (10 fields):
- source, timestamp, symbols, categories, headline, summary, url,
  raw_content (where permitted), sentiment (left blank — Stage 10), provider

**Rule**: No AI analysis at this stage. Sentiment field exists but is null.

### 1.4 Cross-Market Watchlist (16 synchronized instruments)

Continuously monitored:
- SPY, ES, SPX, NQ, QQQ, DIA, IWM, SOXX
- VIX, VVIX, TNX, DXY
- Gold, Oil, Copper, USDJPY

Ensures downstream correlation engines (Stage 9) have synchronized inputs.

### 1.5 Institutional Metadata (10 mandatory fields per record)

Every incoming record MUST carry:

| Field | Type | Description |
|---|---|---|
| `provider` | string | Source provider slug (yahoo, finnhub, polygon, ...) |
| `provider_latency` | int (ms) | Time from request to response |
| `download_timestamp` | ISO 8601 UTC | When ATHENA-X received it |
| `market_timestamp` | ISO 8601 UTC | When the market event occurred |
| `timezone` | string | Original timezone (e.g., "America/New_York") |
| `symbol` | string | Normalized symbol |
| `asset_class` | string | equity / etf / future / index / option / currency / commodity / yield / volatility / crypto |
| `confidence_score` | float (0..1) | Initially provider default (e.g., 0.95 for Databento, 0.85 for Yahoo) |
| `status` | string | fresh / delayed / stale / failed |
| `session` | string | overnight / pre-market / regular / post-market / weekend / holiday |

This metadata is **in addition to** the 10 bus event metadata fields from Stage 1.

### 1.6 Raw Data Archival (never discard)

```
raw_landing/
├── yahoo/
│   └── 2026/
│       └── 07/
│           └── 17/
│               └── 13/
│                   └── <uuid>.json
├── finnhub/
│   └── 2026/07/17/13/<uuid>.json
└── polygon/
    └── 2026/07/17/13/<uuid>.json
```

**Rule**: Every raw payload is archived before parsing. If parsing fails later,
the original is still available for replay/audit.

### 1.7 Provider Health Monitor (per-provider, 7 metrics)

| Metric | Type | Description |
|---|---|---|
| `latency` | float (ms) | Rolling avg response time |
| `success_rate` | float (0..1) | Successful calls / total calls |
| `failure_rate` | float (0..1) | 1 - success_rate |
| `missing_fields` | int | Count of records with missing required fields |
| `staleness` | float (ms) | Age of most recent successful response |
| `api_quota_remaining` | int | API calls remaining in current window |
| `last_successful_update` | ISO 8601 UTC | Timestamp of last success |

Exposed via `/health/providers` endpoint (Stage 16 dashboard).

### 1.8 Session Awareness

Every market record auto-detects:

| Session | Hours (ET) | Behavior |
|---|---|---|
| `overnight` | 20:00 – 04:00 | Low liquidity, futures only |
| `pre-market` | 04:00 – 09:30 | Equity pre-market, widening spreads |
| `regular` | 09:30 – 16:00 | RTH — primary trading session |
| `post-market` | 16:00 – 20:00 | Equity post-market |
| `weekend` | Fri 20:00 – Sun 20:00 | Crypto only |
| `holiday` | NYSE holidays | No US equity session |

**Why this matters**: SPY, SPX, ES behave differently across sessions. The AI
must know which session a data point came from to interpret it correctly.

### 1.9 Data Freshness Tracking

Every stream publishes:
- `expected_update_frequency` (e.g., 1s for ES, 15s for VIX)
- `actual_update_frequency` (rolling avg)
- `last_received_timestamp`
- `status`: fresh / delayed / stale

| Status | Definition |
|---|---|
| `fresh` | last_received within 1.5× expected frequency |
| `delayed` | last_received within 3× expected frequency |
| `stale` | last_received > 3× expected frequency |

**Rule**: Prevents the AI from making decisions on outdated information. Stage 3
(Validation) will reject stale data.

### 1.10 Stage 2 Must Not Calculate

Stage 2 only:
- Download
- Validate basic format
- Timestamp
- Store
- Publish events

Stage 2 must NOT compute: EMA, RSI, MACD, Gamma Exposure, IV Rank, Chan Theory,
Wyckoff, Forecasts, Sentiment. Those belong to later stages.

---

## 2. Stage 2 Exit Criteria (all must pass)

1. ✅ Every configured data source is connected and automatically fails over when needed
2. ✅ Raw data is archived before any transformation
3. ✅ Every record includes complete metadata (10 fields)
4. ✅ Provider health and freshness are continuously monitored
5. ✅ Session detection (overnight, pre-market, regular, post-market) is accurate
6. ✅ Event bus publishes standardized `market:*` events for downstream consumers
7. ✅ The system runs continuously for at least one full trading day without data loss or unhandled failures
8. ✅ All data can be replayed from storage for later backtesting and auditing

---

## 3. Acceptance Tests (6 categories, same as Stage 1)

1. **Functional** — each collector downloads its data type correctly
2. **Integration** — collectors emit `market:*` events on the bus
3. **Data accuracy** — cross-checked against provider data (where feasible without real API keys)
4. **Stress** — 1000 symbols × 5 providers = 5000 concurrent fetches
5. **Failover** — simulate Yahoo outage → automatic switch to Finnhub
6. **Performance** — <500ms per quote fetch, <50ms event-to-bus publish

---

## 4. Implementation Plan

### 4.1 New packages to implement

| Package | Purpose |
|---|---|
| `runtime/institutional-metadata/` | 10 mandatory metadata fields per record |
| `runtime/session-awareness/` | Trading session detection (overnight/pre/regular/post/weekend/holiday) |
| `runtime/raw-archival/` | Filesystem archival (provider/yyyy/mm/dd/hh/) |
| `runtime/data-freshness/` | Fresh/delayed/stale status tracking |
| `providers/base/` | MarketDataProvider protocol (already scaffolded, needs impl) |
| `providers/yahoo/` | Yahoo Finance adapter (real impl) |
| `providers/finnhub/` | Finnhub adapter (real impl) |
| `providers/polygon/` | Polygon adapter (real impl) |
| `providers/flashalpha/` | FlashAlpha adapter (real impl) |
| `providers/fred/` | FRED adapter (real impl) |
| `providers/alphavantage/` | Alpha Vantage adapter (real impl) |
| `providers/databento/` | Databento adapter (real impl) |
| `providers/trading-economics/` | Trading Economics adapter (real impl) |
| `providers/reuters/` | Reuters news adapter (RSS-based) |
| `providers/cnn/` | CNN Business + Fear & Greed adapter |
| `providers/wsj/` | WSJ news adapter (RSS) |
| `providers/cnbc/` | CNBC news adapter (RSS) |
| `providers/sec/` | SEC EDGAR adapter |
| `providers/polymarket/` | Polymarket adapter |
| `providers/simulated/` | Simulated adapter (dev only — never production) |
| `agents/data-collection/market-data/` | 20 market data collectors |
| `agents/data-collection/options-data/` | Options data collectors |
| `agents/data-collection/news-data/` | News collectors (14 sources) |
| `agents/data-collection/cross-market-data/` | 16 synchronized cross-market collectors |

### 4.2 Dependency on Stage 1

Stage 2 builds on:
- `runtime/event-bus/` — for publishing `market:*`, `news:*`, `options:*` events
- `runtime/logger/` — structured logging
- `runtime/config/` — provider API keys, failover chain config
- `runtime/health-monitor/` — provider health tracking
- `runtime/scheduler/` — periodic collection intervals
- `runtime/di/` — wiring collectors into the container
- `runtime/secrets/` — API key access

### 4.3 Implementation order

1. Foundation types: institutional-metadata, session-awareness, raw-archival, data-freshness
2. Provider base protocol + SimulatedProvider (for tests)
3. Real provider adapters (Yahoo first as canonical example, then others)
4. Market data collectors (20 instruments)
5. Options data collectors
6. News collectors (14 sources)
7. Cross-market watchlist
8. Provider health monitor integration
9. Acceptance tests
10. 24-hour continuous run test

---

## 5. Approval

Approved. Proceeding with implementation.
