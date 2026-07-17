# STEP 4 — Stage 10: Market Narrative Intelligence Platform

> **Status**: Approved.
> **Stage 9 status**: ✅ Complete (793 tests, 81 cross-market plugins, Market DNA).
> **Stage 10 purpose**: Answer "Why is the market moving right now, and what events
> could change its direction next?" via Narrative DNA + Catalyst Radar.
> **Rule**: No trade recommendations or forecasts. Only structured market intelligence.

---

## 0. The 4 Intelligence Objects (established by Stage 10)

| # | Object | Stage | Source |
|---|---|---|---|
| 1 | **Technical DNA** | 7 | Technical Snapshot Agent |
| 2 | **Options DNA** | 8 | 0DTE Intelligence Snapshot |
| 3 | **Market DNA** | 9 | Market DNA Agent |
| 4 | **Narrative DNA** | 10 | Market Narrative Agent |

Stages 11+ (Forecast, Probability, Reports, Supervisor) consume these 4 objects
instead of parsing raw inputs.

---

## 1. Architecture (7 layers)

```
News Sources (Stage 2 collectors)
    ↓
News Validation (Stage 3)
    ↓
Event Classification (plugin-based)
    ↓
Cross-Market Correlation
    ↓
Event Impact Assessment
    ↓
Market Narrative Generator
    ↓
ai:news:* / ai:macro:* events
    ↓
Narrative DNA + Catalyst Radar
```

---

## 2. News Categories (10, plugin-based)

| Category | Examples |
|---|---|
| breaking | Reuters, Bloomberg, CNBC, WSJ, CNN |
| economic | CPI, PPI, NFP, GDP, Retail Sales, PMI, ISM, Housing |
| fed | FOMC, Powell, Governors, Beige Book, Minutes |
| treasury | Auctions, Debt Issuance, TGA |
| earnings | MAG7, S&P 500, Nasdaq 100, SOXX |
| geopolitical | Wars, Sanctions, Trade, Taiwan, Middle East |
| energy | OPEC, Oil, LNG, Nat Gas |
| semiconductor | NVDA, AMD, TSMC, AVGO, INTC, QCOM, ARM |
| regulatory | SEC, CFTC, OCC |
| alternative | Polymarket, Company announcements, Gov press releases |

---

## 3. Event Schema

Every news item becomes a structured event:

```
Event ID, Timestamp, Source, Headline, Category, Subcategory,
Symbols, Region, Market, Importance, Confidence, Related Assets, Status
```

---

## 4. Market Impact Engine

Computes directional relationships (not forecasts):

```
Event: US CPI
→ Bonds ↑ → DXY ↑ → VIX ↑ → ES ↓
Probability: 82%
```

---

## 5. Event Timeline

Live timeline of all events for the day.

---

## 6. Narrative Engine

Produces one coherent market narrative:

```
Primary Driver: Stronger-than-expected CPI
Secondary Driver: Higher Treasury yields
Supporting Evidence: DXY strengthening, VIX rising, QQQ underperforming
Current Theme: Inflation Risk
Confidence: 93%
```

---

## 7. Catalyst Radar

Tracks upcoming market-moving events:

- Next 15 minutes
- Next hour
- Today
- This week (CPI, FOMC, NFP, OPEX, Treasury auctions, earnings)

---

## 8. Implementation Plan

| Package | Purpose |
|---|---|
| `plugins/news/_base/` | NewsPlugin Protocol |
| `plugins/news/*/manifest.yaml` | 10+ category manifests |
| `engines/narrative-engine/` | Narrative Engine + Impact Assessment + Event Timeline |
| `agents/narrative-intelligence/` | Narrative DNA Agent + Catalyst Radar Agent |
| `runtime/stage10-integration/` | Acceptance tests |

---

**Approval**: Approved. Proceeding with implementation.
