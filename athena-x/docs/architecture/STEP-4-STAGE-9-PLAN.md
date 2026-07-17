# STEP 4 — Stage 9: Market Intelligence & Correlation Platform

> **Status**: Approved with comprehensive enhancements.
> **Stage 8 status**: ✅ Complete (753 tests, 58 options plugins, stage-gate 6/6 PASS).
> **Stage 9 purpose**: Continuously monitor every market that influences SPY/ES,
> calculate real-time relationships, detect leading indicators, and publish
> synchronized intelligence. Answers: "What is driving ES right now?"

---

## 0. Architecture

```
            Canonical Databases (Stage 5)
                    │
                    ▼
        Cross-Market Plugin Manager
                    │
     ┌──────────────┼──────────────┐
     │              │              │
 Market       Correlation      Leadership
 Monitor         Engine           Engine
     │              │              │
     └──────────────┼──────────────┘
                    │
          Market Intelligence Hub
                    │
            Event Publisher
                    │
        + Market DNA (single summary object)
                    │
        Decision Intelligence (Stage 12)
```

---

## 1. Market Groups (9 groups, 50+ instruments)

| Group | Instruments |
|---|---|
| **Core** | ES ⭐, SPY, SPX, NQ, QQQ |
| **Volatility** | VIX, VVIX, MOVE |
| **Rates** | TNX (10Y), 2Y, 30Y |
| **Currency** | DXY, USDJPY, EURUSD |
| **Commodities** | Gold, Silver, Oil, Nat Gas, Copper |
| **Breadth** | A/D, TICK, TRIN, NYSE Breadth, Volume Breadth, New H/L |
| **Sectors** | XLK, XLF, XLV, XLY, XLI, XLE, XLP, XLB, XLU, XLRE, XLC |
| **Semiconductor** | SOXX, SMH, NVDA, AMD, AVGO, TSM, MU, ARM |
| **MAG7** | AAPL, MSFT, NVDA, AMZN, GOOGL, META, TSLA |
| **Global** | Nikkei, Hang Seng, Shanghai, ASX200, DAX, FTSE, CAC40, EuroStoxx |
| **Crypto** | BTC, ETH |

---

## 2. Plugin Categories (6)

| Category | Plugins |
|---|---|
| **market_monitor** | One per asset (spy, es, vix, dxy, soxx, ...) |
| **correlation** | SPY↔ES, SPY↔VIX, SPY↔DXY, SPY↔TNX, SPY↔Oil, SPY↔Gold, ... |
| **leadership** | Who is leading? Who is lagging? Who is diverging? |
| **regime** | Risk-On, Risk-Off, Inflation, Deflation, Liquidity Exp/Contract |
| **rotation** | Tech→Defensive, Growth→Value, Large→Small, Semi→Software, Cyclical→Utilities |
| **divergence** | spy_es_divergence, vix_not_confirming, breadth_weakening, ... |

---

## 3. Market DNA

Single summary object consumed by all downstream AI:

```
Market DNA
├── Market Regime:    Risk-On
├── Trend:            Bullish
├── Volatility:       Expanding
├── Liquidity:        Neutral
├── Breadth:          Strong
├── Leadership:       Semiconductors
├── Weakest Sector:   Utilities
├── Strongest Asset:  ES
├── Weakest Asset:    VIX
├── Risk Score:       27/100
└── Confidence:       94%
```

Stage 10 (Forecast), Stage 11 (Probability), Stage 12 (Supervisor) consume this
single object instead of querying dozens of individual plugins.

---

## 4. Synchronization Engine

Every few seconds, creates a Market Snapshot with all instruments synchronized.

---

## 5. Implementation Plan

| Package | Purpose |
|---|---|
| `plugins/cross-market/_base/` | CrossMarketPlugin Protocol |
| `plugins/cross-market/*/manifest.yaml` | 50+ market monitor + correlation + leadership manifests |
| `engines/cross-market-plugin-engine/` | Cross-Market Plugin Manager + Correlation Engine + Leadership Engine |
| `agents/market-intelligence/` | Market Intelligence Hub + Market DNA Agent |
| `runtime/stage9-integration/` | Acceptance tests |

---

**Approval**: Approved. Proceeding with implementation.
