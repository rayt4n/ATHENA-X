# STEP 4 — Stage 7 Refactor: Plugin-Based TA Platform

> **Status**: Approved — refactor from hardcoded agents to plugin platform.
> **Previous Stage 7**: 5-layer hierarchy (kept as organizational concept).
> **New approach**: Plugin Manager + Registry + Dependency Graph + Scheduler + Config Service.

---

## 0. Approval Gate

User's verbatim directive:

> "Instead of building a 'Technical Analysis Engine,' build a Technical Analysis
> Platform consisting of: Plugin Manager, Indicator Registry, Dependency Graph,
> Execution Scheduler, Configuration Service, Technical Supervisor."

---

## 1. Architecture

```
Technical Analysis Platform
    │
    ├── Plugin Manager       (discovers, loads, unloads, validates plugins)
    ├── Indicator Registry    (metadata, versions, capabilities)
    ├── Dependency Manager    (resolves calculation dependencies — reuse, don't recalculate)
    ├── Execution Scheduler   (configurable frequencies per indicator)
    ├── Configuration Service (enable/disable plugins without code changes)
    ├── Event Publisher       (all outputs as ai:technical:* events)
    └── Technical Supervisor  (monitors plugin health, performance, errors)
            │
    Load Indicator Plugins
        EMA, SMA, RSI, MACD, VWAP, ADX, ATR, Bollinger,
        Wyckoff, Chan Theory, Elliott, Smart Money, ...
```

**The engine never knows which indicators exist. It only knows how to load plugins.**

---

## 2. Plugin Structure

Every indicator is a self-contained module:

```
plugins/indicators/ema/
├── manifest.yaml    (id, name, version, category, timeframes, inputs, outputs, dependencies, enabled)
├── indicator.py     (implements TechnicalIndicator Protocol)
├── config.py        (plugin-specific configuration)
├── tests/           (independent tests)
└── docs/            (README + API docs)
```

---

## 3. Manifest File

```yaml
id: ema
name: EMA
version: 1.0.0
category: trend          # trend | momentum | volume | structure | pattern | liquidity | projection
layer: 2                  # 1=market_structure, 2=indicator, 3=institutional, 4=consensus
timeframes: [1M, 1W, 1D, 4H, 1H, 30M, 15M, 5M, 1m]
inputs: [OHLCV]
outputs: [ema20, ema50, ema200]
dependencies: []          # no dependencies on other indicators
refresh_interval_seconds: 1
enabled: true
```

The engine reads this automatically. No code changes needed to add an indicator.

---

## 4. Categories

| Category | Indicators |
|---|---|
| **trend** | EMA, SMA, ADX |
| **momentum** | RSI, MACD, Stochastic |
| **volume** | VWAP, Volume Profile, OBV |
| **structure** | Wyckoff, Chan Theory, Smart Money |
| **pattern** | Candlestick, Escape Top, Pull-Up |
| **liquidity** | Liquidity, Support/Resistance |
| **projection** | Elliott Wave, Fibonacci |

---

## 5. Dependency Manager

Some indicators depend on others:

```
MACD → EMA → OHLCV
Wyckoff → Volume Profile → Volume
Bollinger → SMA → OHLCV
```

Instead of recalculating, the Dependency Manager provides existing results.

---

## 6. Execution Scheduler

Each plugin controls its refresh rate:

| Indicator | Refresh |
|---|---|
| EMA | Every tick (1s) |
| VWAP | Every 5 seconds |
| Wyckoff | Every 15 seconds |
| Chan Theory | Every 30 seconds |
| Elliott Wave | Every 1 minute |

---

## 7. Configuration Service

```yaml
enabled:
  ema: true
  sma: true
  macd: true
  rsi: true
  bollinger: false
  elliott: false
  wyckoff: true
```

Turn indicators on/off without restarting.

---

## 8. Hot Installation

Drop a new plugin folder → restart Plugin Manager → engine loads it. No other module changes.

---

## 9. Implementation Plan

### New packages

| Package | Purpose |
|---|---|
| `engines/plugin-engine/` | Plugin Manager + Registry + Dependency Graph + Scheduler + Config |
| `plugins/indicators/_base/` | Already exists (TechnicalIndicator Protocol from Stage 5.1) |
| `plugins/indicators/ema/` | Refactored as self-contained plugin with manifest.yaml |
| `plugins/indicators/rsi/` | Same pattern |
| ... (all 14 indicator plugins refactored) | |
| `runtime/stage7-plugin-integration/` | Acceptance tests for plugin platform |

---

**Approval**: Approved. Proceeding with implementation.
