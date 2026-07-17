# STEP 4 — Stage 7 Plan (Institutional Technical Analysis Engine V1)

> **Status**: Approved with hierarchical 5-layer architecture.
> **Stage 6 status**: ✅ Complete (575 tests, stage-gate 6/6 PASS).
> **Stage 7 purpose**: Transform validated market data into institutional
> technical intelligence — not just indicator values.

---

## 0. Approval Gate

User's verbatim directive:

> "The Technical Analysis Engine should not be designed as '23 separate
> indicators.' It should be designed as a hierarchical intelligence engine...
> organize them into five layers... Rather than requiring every downstream
> module to query 23 different TA agents, this agent would publish a single
> synchronized technical snapshot."

---

## 1. The 5-Layer Architecture

```
Layer 1 — Market Structure          (what the market IS doing)
    ↓
Layer 2 — Indicator Engine           (mathematical calculations only)
    ↓
Layer 3 — Institutional Analysis     (interpret market behavior)
    ↓
Layer 4 — Multi-Timeframe Consensus  (synchronized view across 8 timeframes)
    ↓
Layer 5 — Technical Supervisor       (monitor + health + restart)
    ↓
Technical Snapshot Agent             (single synchronized output for downstream)
```

---

## 2. Layer 1 — Market Structure

These describe **what the market is doing**. Run first because downstream
analyses depend on them.

| Agent | Purpose |
|---|---|
| Multi-Timeframe Data | Fetches + synchronizes OHLCV across 8 timeframes |
| Trend Detection | Bullish / Bearish / Ranging classification |
| Swing High/Low | Identifies pivot points |
| Support & Resistance | Key price levels |
| Liquidity | Liquidity pools + voids |
| Volume Profile | POC / VAH / VAL distribution |

---

## 3. Layer 2 — Indicator Engine

**Mathematical calculations only.** Pure functions. No forecasting. No buy/sell
conclusions. Deterministic outputs.

| Agent | Purpose |
|---|---|
| EMA | Exponential Moving Average |
| SMA | Simple Moving Average |
| VWAP | Volume-Weighted Average Price |
| RSI | Relative Strength Index |
| MACD | Moving Average Convergence Divergence |
| ADX | Average Directional Index |
| ATR | Average True Range |
| Bollinger Bands | Volatility bands |

---

## 4. Layer 3 — Institutional Analysis

These **interpret market behavior**. Consume outputs from Layers 1 + 2 rather
than recalculating.

| Agent | Purpose |
|---|---|
| Wyckoff | Accumulation/Distribution phase detection |
| Chan Theory (缠论) | Bi/Duan/Zhongshu analysis |
| Elliott Wave | Wave pattern recognition |
| Smart Money Concepts | Order blocks, FVGs, smart money footprints |
| Volume-Price Analysis (量价) | Volume-price relationship analysis |
| Escape Top (逃顶) | Breakout-from-consolidation top detection |
| Entry (进场) | High-probability entry identification |
| Pull-Up Pattern (拉升) | Pull-up continuation pattern detection |

---

## 5. Layer 4 — Multi-Timeframe Consensus

**One agent** produces a synchronized view across 8 timeframes.

Timeframes: Monthly → Weekly → Daily → 4H → 1H → 30M → 15M → 5M → 1M

Output example:
```
Long-term Trend:  Bullish
Intermediate:     Bullish
Intraday:          Bearish Pullback
Alignment:         82%
Conflict:          15M diverging from 1H
```

Downstream modules read this single consensus instead of reconciling 8 timeframes.

---

## 6. Layer 5 — Technical Supervisor

Monitors all TA agents.

Responsibilities:
- Detect failed calculations
- Detect stale indicators
- Detect inconsistent timeframes
- Restart failed agents
- Measure latency + calculation duration
- Publish health events

---

## 7. Technical Snapshot Agent (additional)

Publishes a **single synchronized technical snapshot** after all required
analyses complete. This becomes the standard technical input for:
- Options Intelligence (Stage 8)
- Market Intelligence (Stage 10)
- Forecast Engine (Stage 11)
- Report Engine (Stage 15)

---

## 8. Technical Confidence Score

Every TA output includes:
```json
{
  "indicator": "EMA",
  "timeframe": "15m",
  "value": 752.44,
  "confidence": 0.99,
  "quality": "A+"
}
```

For interpretive analyses (Wyckoff, Chan Theory, Elliott Wave), confidence
reflects pattern-recognition agreement.

---

## 9. Shared Timeframe Context

All TA agents evaluate the same 8 timeframes:
Monthly, Weekly, Daily, 4H, 1H, 30M, 15M, 5M, 1M

Prevents subtle inconsistencies.

---

## 10. Calculation Cache

```
Repository → Bar Cache → Indicators
```

EMA, MACD, Bollinger, ATR all use identical OHLCV bars. Instead of querying
repeatedly, a shared bar cache eliminates redundant repository reads.

---

## 11. Standard Technical Event

Every TA result publishes:
```json
{
  "agent": "EMAAgent",
  "symbol": "ES",
  "timeframe": "15m",
  "indicator": "EMA20",
  "value": 7523.50,
  "confidence": 0.99,
  "calculation_time_ms": 4
}
```

---

## 12. Stage 7 Exit Criteria

1. ✅ All 23 TA agents implement the TechnicalIndicator Protocol
2. ✅ Every agent reads exclusively from the Canonical Repository
3. ✅ No TA agent writes directly to the database
4. ✅ All outputs emitted as standardized `ai:technical:*` events
5. ✅ Multi-timeframe synchronization (Monthly → 5M) working consistently
6. ✅ Timeframe Consensus Agent publishes unified market view
7. ✅ Interpretive agents consume lower-layer outputs (no recalculation)
8. ✅ Technical Supervisor monitors latency, freshness, failures, sync
9. ✅ Shared bar caching eliminates redundant repository reads
10. ✅ All 6 stage-gate criteria pass

---

## 13. Implementation Plan

### New packages

| Package | Layer | Purpose |
|---|---|---|
| `agents/technical-analysis/_base/` | infra | BaseTAAgent + bar cache + shared timeframe context |
| `agents/technical-analysis/layer1-market-structure/` | 1 | 6 agents (trend, swing, S/R, liquidity, volume profile, multi-TF data) |
| `agents/technical-analysis/layer2-indicators/` | 2 | 8 agents (EMA, SMA, VWAP, RSI, MACD, ADX, ATR, Bollinger) |
| `agents/technical-analysis/layer3-institutional/` | 3 | 8 agents (Wyckoff, Chan, Elliott, Smart Money, Vol-Price, Escape Top, Entry, Pull-Up) |
| `agents/technical-analysis/layer4-consensus/` | 4 | 1 agent (Multi-Timeframe Consensus) |
| `agents/technical-analysis/layer5-supervisor/` | 5 | 1 agent (Technical Supervisor) |
| `agents/technical-analysis/snapshot/` | 6 | 1 agent (Technical Snapshot) |
| `runtime/stage7-integration/` | test | End-to-end wiring + acceptance tests |

---

**Approval**: Approved. Proceeding with implementation.
