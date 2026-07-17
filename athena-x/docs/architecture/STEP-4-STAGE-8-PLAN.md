# STEP 4 — Stage 8: Institutional Options Intelligence Platform (V1)

> **Status**: Approved with plugin-based architecture.
> **Stage 7 status**: ✅ Complete (plugin-based TA platform, 721 tests, stage-gate 6/6 PASS).
> **Stage 8 purpose**: Modular, real-time options intelligence platform where every metric
> is an independent plugin. Optimized for SPY/ES/SPX 0DTE institutional trading.

---

## 0. Architecture

```
            Options Data (from Stage 2 collectors)
                     │
                     ▼
          Canonical Options Database (Stage 5)
                     │
                     ▼
          Options Plugin Manager (reuses Stage 7 plugin engine)
                     │
     ┌───────────────┼────────────────┐
     │               │                │
 Volatility       Greeks          Flow
     │               │                │
 Dealer Pos      Gamma           Risk
     │               │                │
             Event Publisher
                     │
             ai:options:* events
                     │
             AI Decision Agents (Stage 12)
```

**The engine doesn't know about Gamma Flip, Max Pain, or IV Rank directly. It only loads plugins.**

---

## 1. Plugin Categories (8)

| # | Category | Plugins |
|---|---|---|
| 1 | **volatility** | IV, IV Rank, IV Percentile, Historical Vol, Realized Vol, Vol Surface, Vol Smile, Term Structure, Expected Move, IV Crush Probability |
| 2 | **greeks** | Delta, Gamma, Theta, Vega, Rho, Charm, Vanna, Vomma, Speed, Color |
| 3 | **dealer** | GEX, Dealer Delta, Dealer Gamma, Dealer Hedging Pressure, Gamma Flip, Dealer Inventory, Positive Gamma Zone, Negative Gamma Zone |
| 4 | **flow** | Option Flow, Sweep Orders, Block Trades, Unusual Activity, Large Orders, Smart Money Detection, Whale Activity |
| 5 | **open_interest** | Call OI, Put OI, OI Change, OI Build-up, Strike Concentration, OI Walls |
| 6 | **0dte** | 0DTE Call Flow, 0DTE Put Flow, Opening/Midday/Closing Positioning, Dealer Hedging, Gamma Acceleration, Intraday Risk |
| 7 | **dark_pool** | Dark Pool Trades, Block Prints, ATS Volume, Hidden Liquidity, Institutional Accumulation |
| 8 | **probability** | Probability of Profit, Probability ITM, Probability OTM, Pin Probability, Expiration Distribution |

---

## 2. Plugin Structure

```
plugins/options/gamma_flip/
├── manifest.yaml    (id, name, version, category, refresh_interval, inputs, outputs, dependencies)
├── plugin.py        (implements OptionsPlugin protocol)
├── config.py
├── tests/
└── docs/
```

---

## 3. Scheduling

| Metric | Refresh |
|---|---|
| Greeks | 1 second |
| Option Flow | Real time (event-driven) |
| Dealer Position | 5 seconds |
| Gamma Exposure | 10 seconds |
| Max Pain | 1 minute |
| IV Rank | 1 minute |
| Expected Move | 1 minute |
| Probability | 1 minute |

---

## 4. SPY 0DTE Intelligence Layer

A dedicated aggregation layer producing:

- Current Gamma Flip
- Dealer Long/Short Gamma
- Major Call/Put Walls
- Expected Move
- Max Pain
- 0DTE Positioning
- IV Regime
- IV Crush Risk
- Theta Decay Rate
- Dealer Hedge Direction
- Breakout Probability
- Mean Reversion Probability

---

## 5. Output Events

```
options:gamma_updated
options:dealer_position_changed
options:iv_updated
options:max_pain_updated
options:flow_detected
options:dark_pool_detected
options:expected_move_changed
options:0dte_positioning_changed
```

---

## 6. Implementation Plan

### New packages

| Package | Purpose |
|---|---|
| `plugins/options/_base/` | OptionsPlugin Protocol (stable interface) |
| `plugins/options/*/manifest.yaml` | 40+ plugin manifests (self-contained) |
| `engines/options-plugin-engine/` | Options Plugin Manager (reuses Stage 7 plugin engine) |
| `agents/options-intelligence/` | Options Intelligence Agent (0DTE aggregation layer) |
| `runtime/stage8-integration/` | Acceptance tests |

---

**Approval**: Approved. Proceeding with implementation.
