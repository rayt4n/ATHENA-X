# ATHENA-X — STEP 2: Modular Architecture Redesign

> Paradigm: **Modules, not pages. Like Bloomberg.**
> Constraint: No code in this document. This is the design that STEP 3 (folder skeleton) and STEP 4 (per-module implementation) will follow.
> Output: A complete architectural specification that an engineer can implement module-by-module without ambiguity.

---

## 0. Design Principles (non-negotiable)

These principles govern every decision in this document and every line of code in STEP 4:

1. **Module = the atomic unit.** A module is an independently launchable, independently testable, independently replaceable unit of functionality. Modules are NOT routes. They are NOT pages. They are runtime entities that can be opened in panels, run headless in the background, and compose into workspaces.
2. **A workspace is a composition of running module instances**, not a navigation tree. The user opens a workspace, the workspace hosts N panel instances and M background services, all running concurrently, all talking through the bus.
3. **The message bus is the only cross-module communication channel.** Modules never call each other directly. They publish events. They subscribe to events. They expose a public API façade that other modules may invoke — but even that goes through the bus when it's an agent-to-agent call.
4. **AI is hybrid and routed.** Fast models (Logistic, RF, small GBM) run in-browser via ONNX Runtime Web. Heavy models (LSTM, Transformer, TabPFN, XGBoost, CatBoost, LightGBM-large) run on a Python GPU backend. LSTM NEVER runs in the browser. The router is explicit and configurable.
5. **Backtesting is real.** Never mock. The Self Validation module runs actual Python vectorbt backtests over historical data. Trade history is computed, not invented.
6. **Data is real.** Yahoo → Finnhub → Polygon → FlashAlpha → FRED → AlphaVantage failover chain. If all providers fail, the system fails honestly — it does not fall back to mock in production.
7. **Reports are multi-format.** Markdown → JSON → PDF → Supabase Storage → Dashboard. One report, four artifacts, all persisted.
8. **Institutional dark only.** No light theme. No playful animations. The aesthetic is Bloomberg / Refinitiv / FactSet — dense, monospaced numerics, OKLCH green/red, grid background, status banners, keyboard-first.
9. **Per-user, workspace-aware.** Auth is per-user. Each user has multiple workspaces. Each workspace has its own panel layout, watchlist, and background services.
10. **No placeholders, no TODOs, no dead code, no circular imports.** Enforced by lint + typecheck + tests after every module.

---

## 1. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER (browser)                                  │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │                  NEXT.JS DASHBOARD (Vercel)                            │  │
│  │                                                                        │  │
│  │  ┌──────────────┐  ┌──────────────────────────────────────────────┐   │  │
│  │  │  Workspace   │  │  Module Instances (running in panels)         │   │  │
│  │  │  Shell       │  │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐         │   │  │
│  │  │  - panels    │  │  │ TA   │ │ TA   │ │ NEWS │ │ MKT  │  ...    │   │  │
│  │  │  - palette   │  │  │NVDA  │ │AAPL  │ │      │ │      │         │   │  │
│  │  │  - status    │  │  └──────┘ └──────┘ └──────┘ └──────┘         │   │  │
│  │  │  - ticker    │  │  Each instance = its own Zustand slice       │   │  │
│  │  └──────┬───────┘  │  + TanStack Query cache                       │   │  │
│  │         │          │  + ONNX Runtime Web (fast AI)                 │   │  │
│  │         │          └────────────┬─────────────────────────────────┘   │  │
│  │         │                       │                                     │  │
│  │         ▼                       ▼                                     │  │
│  │  ┌──────────────────────────────────────────────────────────────┐    │  │
│  │  │             FRONTEND EVENT BUS (typed pub/sub)                │    │  │
│  │  │   - React context + Zustand middleware                       │    │  │
│  │  │   - WebSocket bridge to backend bus                          │    │  │
│  │  └──────────────────────┬───────────────────────────────────────┘    │  │
│  └─────────────────────────┼────────────────────────────────────────────┘  │
└────────────────────────────┼───────────────────────────────────────────────┘
                             │
                             │  WebSocket (events) + HTTPS (API)
                             │
┌────────────────────────────┼───────────────────────────────────────────────┐
│                            ▼                                                 │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │              PYTHON BACKEND (GPU instance)                              │ │
│  │                                                                        │ │
│  │  ┌──────────────┐  ┌──────────────────────────────────────────────┐  │ │
│  │  │  FastAPI     │  │  Backend Agents (always running)              │  │ │
│  │  │  routers:    │  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ │  │ │
│  │  │  - market    │  │  │TA-Agt  │ │News-Agt│ │Opt-Agt │ │Mac-Agt │ │  │ │
│  │  │  - ta        │  │  └────────┘ └────────┘ └────────┘ └────────┘ │  │ │
│  │  │  - options   │  │  ┌────────┐ ┌────────┐ ┌────────┐             │  │ │
│  │  │  - news      │  │  │Fcst-Agt│ │Prob-Agt│ │Val-Agt │             │  │ │
│  │  │  - macro     │  │  └────────┘ └────────┘ └────────┘             │  │ │
│  │  │  - forecast  │  └──────────────────────────────────────────────┘  │ │
│  │  │  - prob      │                                                    │ │
│  │  │  - validator │  ┌──────────────────────────────────────────────┐ │ │
│  │  │  - report    │  │  AI Runtime (GPU)                            │ │ │
│  │  └──────┬───────┘  │  - PyTorch: LSTM, Transformer                │ │ │
│  │         │          │  - TabPFN                                    │ │ │
│  │         │          │  - XGBoost, CatBoost, LightGBM               │ │ │
│  │         │          │  - ONNX Runtime (fallback)                   │ │ │
│  │         │          └──────────────────────────────────────────────┘ │ │
│  │         │                                                            │ │
│  │         ▼                                                            │ │
│  │  ┌──────────────────────────────────────────────────────────────┐  │ │
│  │  │             BACKEND EVENT BUS (Redis Pub/Sub + NATS)         │  │ │
│  │  │   - All agents publish/subscribe here                       │  │ │
│  │  │   - WebSocket bridge mirrors events to frontend             │  │ │
│  │  └──────────────────────┬───────────────────────────────────────┘  │ │
│  └─────────────────────────┼──────────────────────────────────────────┘ │
└────────────────────────────┼─────────────────────────────────────────────┘
                             │
                             │  SQL + Realtime + Storage
                             │
┌────────────────────────────┼─────────────────────────────────────────────┐
│                            ▼                                               │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │                        SUPABASE                                     │  │
│  │  - Postgres (auth, workspaces, watchlists, reports, backtests)    │  │
│  │  - Auth (per-user, workspace-aware, RLS)                          │  │
│  │  - Realtime (subscribe to row changes)                            │  │
│  │  - Storage (PDF reports, model artifacts, exports)                │  │
│  └────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────┘

External data providers (called from Python backend only):
  Yahoo → Finnhub → Polygon → FlashAlpha → FRED → AlphaVantage
```

---

## 2. The Module Contract (canonical)

Every module in ATHENA-X implements this contract. No exceptions.

### 2.1 Module Manifest

Each module declares a **manifest** — a static description of what it is, what it can do, and what events it consumes/produces. The manifest is registered in the module registry at boot time.

```
ModuleManifest {
  id:           ModuleId             // unique slug, e.g. "technical-analysis"
  name:         string               // display name, e.g. "Technical Analysis"
  shortcut:     string               // Bloomberg-style command, e.g. "TA"
  description:  string               // one-line description
  icon:         LucideIcon           // icon for palette and panel header
  version:      string               // semver

  capabilities: {
    launchable:      boolean         // can be opened as a panel (UI)
    multiInstance:   boolean         // can run multiple instances concurrently
    headless:        boolean         // can run as a background service
    defaultHotkey:   string          // keyboard shortcut, e.g. "g t"
  }

  configSchema:    ZodSchema         // validates instance config
  instanceState:   ZodSchema         // validates per-instance runtime state

  subscriptions:  EventBusPattern[]  // events this module reacts to
  publications:   EventBusPattern[]  // events this module emits

  publicAPI:      ModulePublicAPI    // façade other modules may invoke
  panelComponent: ReactComponent     // the UI to render in a panel (if launchable)
  agentFactory:   AgentFactory       // creates a headless agent (if headless)
}
```

### 2.2 Module Instance

A module can be **instantiated** — meaning a running copy with its own config and state. Multiple instances of the same module can run concurrently (e.g., two TA panels: one for NVDA, one for AAPL).

```
ModuleInstance {
  id:         string             // unique instance id (UUID, different from module id)
  moduleId:   ModuleId           // which module this is an instance of
  config:     ModuleConfig       // instance-specific config (symbol, timeframe, etc.)
  state:      ModuleState        // runtime state (loading, ready, error)
  createdAt:  timestamp
}
```

### 2.3 Module Public API (façade)

Each module exposes a **public API** through its `index.ts`. Other modules may ONLY import from this façade. Reaching into a module's internal files is an ESLint error.

```
ModulePublicAPI {
  // Query the module's current state (read-only, no side effects)
  queries: {
    [name: string]: (args) => Result
  }

  // Command the module to do something (side-effectful)
  commands: {
    [name: string]: (args) => Result
  }

  // Subscribe to the module's emitted events
  events: {
    [eventName: string]: EventBusPattern
  }
}
```

### 2.4 Agent (headless variant)

A headless module runs an **agent** — a long-lived process that subscribes to events and publishes events. Agents have no UI. They live on the Python backend (for I/O-heavy and GPU work) or as Web Workers in the browser (for CPU-light tasks).

```
Agent {
  id:           string             // "ta-agent", "forecast-agent", etc.
  moduleId:     ModuleId
  start(config): Promise<void>
  stop():        Promise<void>
  onEvent(event: BusEvent): void   // react to incoming events
  // (agents publish via injected bus.publish())
}
```

---

## 3. Module Catalog (the 10 Bloomberg-style functions)

Each module maps to a Bloomberg-style command. The command palette (Ctrl+K) lets users launch any module by typing its shortcut.

| # | Module ID | Shortcut | Name | Launchable | Multi-Instance | Headless | Default Hotkey |
|---|---|---|---|---|---|---|---|
| 01 | `dashboard` | `DASH` | Dashboard | ✓ | ✗ | ✗ | `g d` |
| 02 | `live-market` | `MKT` | Live Market Data | ✓ | ✓ | ✓ | `g m` |
| 03 | `technical-analysis` | `TA` | Technical Analysis | ✓ | ✓ | ✓ | `g t` |
| 04 | `news-intelligence` | `NEWS` | News Intelligence | ✓ | ✗ | ✓ | `g n` |
| 05 | `options-intelligence` | `OPT` | Options Intelligence | ✓ | ✓ | ✓ | `g o` |
| 06 | `macro-intelligence` | `MACRO` | Macro Intelligence | ✓ | ✗ | ✓ | `g g` |
| 07 | `ai-forecast` | `FCST` | AI Forecast Engine | ✓ | ✓ | ✓ | `g f` |
| 08 | `probability-engine` | `PROB` | Probability Engine | ✓ | ✓ | ✗ | `g p` |
| 09 | `report-generator` | `RPT` | Report Generator | ✓ | ✗ | ✗ | `g r` |
| 10 | `self-validation` | `VAL` | Self Validation | ✓ | ✓ | ✓ | `g v` |

### 3.1 Per-module specifications

**01 Dashboard (`DASH`)** — *Composite workspace view*
- Launchable: yes (default workspace)
- Multi-instance: no (it IS the workspace root)
- Headless: no
- Subscribes to: ALL events (it's the aggregation layer)
- Publishes: `ui:layout-updated`, `ui:widget-added`, `ui:widget-removed`
- Public API: `queries.listWidgets()`, `queries.getLayout()`, `commands.addWidget()`, `commands.removeWidget()`, `commands.resetLayout()`
- Panels: Market Overview, Watchlist, Cross-Module Signals, Price Chart, News Pulse, Market Health, Sector Heatmap — all reorderable/removable via PanelChrome

**02 Live Market Data (`MKT`)** — *Real-time data ingestion*
- Launchable: yes (panel)
- Multi-instance: yes (one per asset class: equities, futures, FX, commodities, rates)
- Headless: yes (MarketDataIngestor agent always running on backend)
- Subscribes to: nothing (it's a source)
- Publishes: `market:quote-updated`, `market:trade-printed`, `market:level2-updated`, `market:provider-failed-over`
- Public API: `queries.getQuote(symbol)`, `queries.getLevel2(symbol)`, `queries.getProviderStatus()`, `commands.forceProvider(name)`
- Provider chain: Yahoo → Finnhub → Polygon → FlashAlpha → FRED → AlphaVantage (managed by backend agent, failover is automatic and event-published)
- Panels: Provider Adapters table (REAL — clicks actually force failover), WebSocket Manager (REAL — connection status), REST Fallback (REAL), Cache + Throttle (REAL metrics), Reconnection (REAL), Quote Board (6 tabs), Order Book Depth, MAG7 Matrix, World Markets, Yield Curve, Commodities, Currencies, TradingView Advanced Chart (wrapped to emit `ui:symbol-selected`)

**03 Technical Analysis (`TA`)** — *Indicator engine*
- Launchable: yes
- Multi-instance: yes (one per symbol — the killer feature)
- Headless: yes (TAEngine agent computes indicators for the watchlist in the background)
- Subscribes to: `market:quote-updated`, `ui:symbol-selected`, `ui:timeframe-changed`
- Publishes: `ta:indicator-computed`, `ta:signal-emitted`, `ta:level-identified`
- Public API: `queries.getIndicators(symbol, timeframe)`, `queries.getSignal(symbol)`, `queries.getLevels(symbol)`, `commands.recompute(symbol)`
- Backend: pandas-ta for indicator computation (RSI, MACD, SMA, EMA, Bollinger, Stochastic, ADX, CCI, Williams %R)
- Panels: Symbol header, Price Action (MA20/MA50/BB toggles), Overall Signal, Key Levels, Indicator Matrix (10 indicators × 4 columns)

**04 News Intelligence (`NEWS`)** — *News + sentiment*
- Launchable: yes
- Multi-instance: no (single feed, filterable)
- Headless: yes (NewsAgent always ingests from RSS + provider APIs)
- Subscribes to: `news:headline-received` (sentiment scorer reacts), `ui:symbol-selected`
- Publishes: `news:headline-received`, `news:sentiment-scored`, `news:impact-classified`, `news:entity-mentioned`
- Public API: `queries.getFeed(filter)`, `queries.getSentiment(symbol)`, `queries.getEntities()`
- Backend: HuggingFace Transformers (FinBERT) for sentiment + impact classification
- Panels: 4 KPI cards, News Feed (search + category filter + sentiment filter), Sentiment Breakdown, Entity Mentions, Impact Distribution

**05 Options Intelligence (`OPT`)** — *Options chain + IV + Greeks*
- Launchable: yes
- Multi-instance: yes (one per symbol)
- Headless: yes (OptionsEngine refreshes chains on schedule)
- Subscribes to: `market:quote-updated`, `ui:symbol-selected`
- Publishes: `options:chain-refreshed`, `options:unusual-activity`, `options:iv-updated`, `options:greek-computed`
- Public API: `queries.getChain(symbol, expiry)`, `queries.getIVSkew(symbol)`, `queries.getUnusualActivity()`, `queries.getIVTermStructure(symbol)`
- Backend: Black-Scholes for Greeks, IV computation via Brent's method
- Panels: IV Skew, Open Interest by Strike, Options Chain (Calls/Both/Puts), Unusual Options Activity, IV Term Structure

**06 Macro Intelligence (`MACRO`)** — *Macro indicators + yield curve*
- Launchable: yes
- Multi-instance: no
- Headless: yes (MacroAgent always ingests from FRED + other sources)
- Subscribes to: nothing (source)
- Publishes: `macro:indicator-released`, `macro:yield-curve-updated`, `macro:fx-rate-updated`, `macro:commodity-updated`
- Public API: `queries.getIndicators(region)`, `queries.getYieldCurve()`, `queries.getFXRates()`, `queries.getCommodities()`
- Backend: FRED API for US, ECB for EU, PBoC for CN, BoJ for JP, ONS for UK
- Panels: US Treasury Yield Curve, 10Y vs 2Y (90D History), Economic Indicators table (region filter), FX Rates, Commodities

**07 AI Forecast Engine (`FCST`)** — *Hybrid AI ensemble*
- Launchable: yes
- Multi-instance: yes (one per symbol)
- Headless: yes (ForecastAgent runs on schedule — every 5min during market hours)
- Subscribes to: `market:quote-updated`, `ta:signal-emitted`, `news:sentiment-scored`, `options:iv-updated`, `macro:indicator-released`, `ui:forecast-rerun`
- Publishes: `forecast:trajectory-computed`, `forecast:scenario-updated`, `forecast:catalyst-detected`, `forecast:confidence-updated`
- Public API: `queries.getForecast(symbol, horizon)`, `queries.getEnsemble(symbol)`, `queries.getScenarios(symbol)`, `queries.getCatalysts(symbol)`, `commands.rerun(symbol, config)`
- AI routing (explicit, never overridden):
  - **LSTM** → Python GPU (PyTorch) — NEVER browser
  - **Transformer** → Python GPU (PyTorch) — NEVER browser
  - **TabPFN** → Python GPU
  - **XGBoost** → Python GPU
  - **CatBoost** → Python GPU
  - **LightGBM (large)** → Python GPU
  - **LightGBM (small)** → Browser ONNX
  - **Random Forest** → Browser ONNX
  - **Logistic Regression** → Browser ONNX
- Panels: Symbol header + horizon + Re-run, Price Forecast Trajectory, Model Ensemble Breakdown (shows which models ran where), Scenario Analysis (Bull/Base/Bear), Forecast Catalysts

**08 Probability Engine (`PROB`)** — *Monte Carlo*
- Launchable: yes
- Multi-instance: yes (one per symbol + strategy)
- Headless: no (on-demand, CPU-heavy)
- Subscribes to: `market:quote-updated`, `options:iv-updated`, `forecast:trajectory-computed`, `ui:simulation-config-changed`
- Publishes: `probability:simulation-run`, `probability:profit-scored`, `probability:strategy-matrix-updated`
- Public API: `queries.getSimulation(symbol, config)`, `queries.getProfitProbability(symbol, strategy)`, `commands.runSimulation(symbol, config)`
- Backend: numpy Monte Carlo with GPU acceleration where available (CuPy)
- Panels: 3 sliders (DTE, simulations, threshold), Monte Carlo Paths, Probability of Profit, Terminal Price Distribution, Strategy Probability Matrix

**09 Report Generator (`RPT`)** — *Multi-format report generation*
- Launchable: yes
- Multi-instance: no
- Headless: no (on-demand)
- Subscribes to: ALL events (it composes from every module's public API)
- Publishes: `report:generation-started`, `report:generation-completed`, `report:exported`, `report:stored`
- Public API: `queries.getReport(id)`, `queries.listReports()`, `commands.generate(config)`, `commands.export(id, format)`
- Output pipeline: Markdown (canonical) → JSON (structured) → PDF (printable) → Supabase Storage (persisted) → Dashboard list (visible)
- Sections: Executive Summary, Market Snapshot, Technical Analysis, News & Sentiment, Options Intelligence, Macro Context, AI Forecast, Risk Assessment, Final Recommendation
- Audiences: Investment Committee, Portfolio Manager, Trader/Execution, Client/Advisor, Research Distribution

**10 Self Validation (`VAL`)** — *Real Python backtesting*
- Launchable: yes
- Multi-instance: yes (one per strategy)
- Headless: yes (ValidatorAgent runs nightly full backtests; on-demand for user-triggered)
- Subscribes to: `forecast:trajectory-computed`, `probability:profit-scored`, `ui:strategy-selected`, `ui:backtest-triggered`
- Publishes: `validator:backtest-run`, `validator:calibration-updated`, `validator:strategy-compared`, `validator:trade-recorded`
- Public API: `queries.getBacktest(strategyId)`, `queries.getEquityCurve(strategyId)`, `queries.getTradeHistory(strategyId)`, `queries.getCalibration(strategyId)`, `commands.runBacktest(strategyId, config)`
- Backend: **vectorbt** for real backtesting. Never mock. Historical data from market_data service. Strategies: ATHENA-X Ensemble, TA-only, News-only, Options-only, Macro-only, AI-Forecast-only
- Models audited: LSTM, Transformer-Seq, TabPFN, GBM (XGBoost/CatBoost/LightGBM ensemble), Random Forest, Logistic Baseline
- Panels: Strategy selector, Equity Curve & Drawdown, Strategy Comparison, Model Performance Audit, Probability Calibration, Trade History (real), PnL Distribution, Monthly Returns Heatmap

---

## 4. The Message Bus

The bus is the central nervous system. Every cross-module interaction goes through it.

### 4.1 Topology

```
┌────────────────────────────────────────────────────────────────────┐
│                     FRONTEND EVENT BUS                              │
│  (in-process pub/sub, TypeScript discriminated union)              │
│                                                                    │
│  React components subscribe via useBusSubscription(pattern)        │
│  Zustand stores publish via bus.publish(event)                     │
│                                                                    │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  WebSocket Bridge                                          │    │
│  │  - Subscribes to backend bus                               │    │
│  │  - Mirrors backend events into frontend bus                │    │
│  │  - Forwards frontend events to backend (selected ones)     │    │
│  └────────────────────────────────────────────────────────────┘    │
└────────────────────────────────────────────────────────────────────┘
                              ↕ WebSocket
┌────────────────────────────────────────────────────────────────────┐
│                     BACKEND EVENT BUS                               │
│  (Redis Pub/Sub for fan-out + NATS for queue semantics)            │
│                                                                    │
│  Python agents subscribe via bus.subscribe(pattern, handler)       │
│  Python agents publish via bus.publish(event)                      │
│                                                                    │
│  Schema: Pydantic v2 models generated from the same OpenAPI spec   │
│  that produces the TypeScript discriminated union                  │
└────────────────────────────────────────────────────────────────────┘
```

### 4.2 Event taxonomy

All events are typed discriminated unions. The schema is the **single source of truth** — both frontend (TypeScript) and backend (Pydantic) are generated from the same OpenAPI spec.

**Event namespace convention**: `<domain>:<subject>-<verb>` (kebab-case)

```
market:                          // source: live-market
  quote-updated                  // { symbol, last, bid, ask, high, low, vol, ts }
  trade-printed                  // { symbol, price, size, side, ts }
  level2-updated                 // { symbol, bids: [[price,size]], asks: [[price,size]], ts }
  provider-failed-over           // { from, to, reason, ts }

news:                            // source: news-intelligence
  headline-received              // { id, headline, source, url, ts, symbols, category }
  sentiment-scored               // { id, sentiment, score, model }
  impact-classified              // { id, impact, confidence }
  entity-mentioned               // { entity, type, count }

ta:                              // source: technical-analysis
  indicator-computed             // { symbol, timeframe, indicator, value, signal }
  signal-emitted                 // { symbol, direction, strength, weight, source: 'TA' }
  level-identified               // { symbol, level, type: 'support'|'resistance', strength }

options:                         // source: options-intelligence
  chain-refreshed                // { symbol, expiry, chain }
  unusual-activity               // { symbol, strike, expiry, type, size, premium }
  iv-updated                     // { symbol, iv, ivSkew, ivTerm }
  greek-computed                 // { symbol, strike, expiry, delta, gamma, theta, vega, rho }

macro:                           // source: macro-intelligence
  indicator-released             // { indicator, region, value, previous, surprise }
  yield-curve-updated            // { points: [{ tenor, yield }], ts }
  fx-rate-updated                // { pair, rate, change }
  commodity-updated              // { commodity, price, change }

forecast:                        // source: ai-forecast
  trajectory-computed            // { symbol, horizon, points: [{ t, price, confidence }] }
  scenario-updated               // { symbol, bull, base, bear, probabilities }
  catalyst-detected              // { symbol, catalyst, impact, ts }
  confidence-updated             // { symbol, model, confidence }
  rerun-requested                // UI → backend

probability:                     // source: probability-engine
  simulation-run                 // { symbol, config, paths, stats }
  profit-scored                  // { symbol, strategy, probability, expectedValue }
  strategy-matrix-updated        // { symbol, matrix: [{ strategy, pop, ev, risk }] }

validator:                       // source: self-validation
  backtest-run                   // { strategyId, config, results }
  calibration-updated            // { model, buckets: [{ predicted, actual }] }
  strategy-compared              // { strategies: [{ id, returns, sharpe, dd }] }
  trade-recorded                 // { strategyId, trade: {...} }

report:                          // source: report-generator
  generation-started             // { reportId, config }
  generation-completed           // { reportId, markdown, json, pdfUrl }
  exported                       // { reportId, format, url }
  stored                         // { reportId, storagePath }

ui:                              // source: any UI module
  symbol-selected                // { symbol, source: 'sidebar'|'palette'|'chart'|'watchlist' }
  module-launched                // { moduleId, instanceId, config }
  module-closed                  // { instanceId }
  layout-updated                 // { workspaceId, layout }
  widget-added                   // { widget }
  widget-removed                 // { widgetId }
  timeframe-changed              // { timeframe }
  main-indicator-switched        // { indicator: 'ES' | 'SPY' }   ← switchable main indicator

system:                          // infrastructure
  agent-started                  // { agentId, moduleId }
  agent-stopped                  // { agentId }
  agent-error                    // { agentId, error }
  bus-connected                  // { transport }
  bus-disconnected               // { reason }
```

### 4.3 Event delivery semantics

- **At-most-once** for high-frequency market data (quotes, trades, level2) — drops are acceptable, last-value-wins.
- **At-least-once** for everything else — consumers must be idempotent. Every event has a unique `eventId` for deduplication.
- **Ordered** per `symbol` for `market:*` and `ta:*` events — consumers can rely on ordering within a symbol stream.
- **Backpressure**: the frontend bus drops market data events older than 500ms if the UI is behind.

### 4.4 Switchable main indicator (ES / SPY)

Per requirement #2.2: the workspace has a **main indicator** setting that can be switched between ES (E-mini S&P 500 Futures) and SPY (SPDR S&P 500 ETF Trust). Switching emits `ui:main-indicator-switched` which:

- Updates the ticker tape primary symbol
- Updates the default symbol for newly-launched modules
- Updates the Market Overview first tile
- Persists to the workspace record in Supabase

---

## 5. Workspace Model

A workspace is the user's runtime composition of module instances.

```
Workspace {
  id:                string            // UUID
  userId:            string            // Supabase auth user id
  name:              string            // "Default", "NVDA focus", etc.
  mainIndicator:     'ES' | 'SPY'      // switchable
  watchlist:         WatchlistSymbol[]
  panelLayout:       PanelLayout       // react-grid-layout compatible
  backgroundServices: BackgroundServiceConfig[]   // which headless agents run
  settings:          WorkspaceSettings // refresh rates, theme overrides, etc.
  createdAt:         timestamp
  updatedAt:         timestamp
}

PanelLayout {
  cols:    12
  rows:    12
  panels:  Panel[]
}

Panel {
  id:                string            // UUID
  moduleInstanceId:  string            // → ModuleInstance.id
  title:             string            // "TA — NVDA"
  x, y, w, h:        number            // grid coords
  minimized:         boolean
  maximized:         boolean
}

BackgroundServiceConfig {
  moduleId:      ModuleId              // e.g., 'forecast'
  enabled:       boolean
  config:        ModuleConfig          // agent-specific config
}
```

### 5.1 Workspace state management

- **Zustand store**: `useWorkspaceStore` — single source of truth for the active workspace's panel layout and module instances.
- **Persistence**: every change is debounced (500ms) and synced to Supabase via TanStack Query mutation.
- **Realtime**: other devices/sessions see workspace changes via Supabase Realtime subscriptions.
- **Undo/redo**: `zundo` middleware on the workspace store.

### 5.2 Multi-instance module instances

Each module instance has its own Zustand slice, keyed by `instanceId`. Example:

```
useModuleInstanceState<TAState>(instanceId)   // selector hook
```

This allows two TA panels — one for NVDA, one for AAPL — to have independent state, independent config, independent subscriptions.

---

## 6. AI Runtime Architecture (Hybrid)

### 6.1 Routing decision table

The router is **explicit and non-overridable**. LSTM and Transformer NEVER run in the browser.

| Model | Runtime | Where | Why |
|---|---|---|---|
| LSTM | PyTorch | Python GPU | Sequential model, GPU-required, NEVER browser |
| Transformer (Seq) | PyTorch | Python GPU | Attention is O(n²), GPU-required, NEVER browser |
| TabPFN | TabPFN lib | Python GPU | In-context learning, GPU-required |
| XGBoost | xgboost | Python GPU | Tree ensemble, large trees need GPU |
| CatBoost | catboost | Python GPU | Symmetric trees, GPU acceleration |
| LightGBM (large) | lightgbm | Python GPU | Large num_iterations, GPU |
| LightGBM (small) | ONNX Runtime | Browser | Small models export to ONNX cleanly |
| Random Forest | ONNX Runtime | Browser | Small, fast, ONNX-native |
| Logistic Regression | ONNX Runtime | Browser | Trivial, ONNX-native |

### 6.2 AI Router contract

```
AIRouter {
  infer(request: InferenceRequest): Promise<InferenceResponse>
}

InferenceRequest {
  modelId:    ModelId        // 'lstm' | 'transformer' | 'tabpfn' | 'xgboost' | ...
  symbol:     string
  inputs:     ModelInputs    // model-specific
  horizon:    number         // bars forward
  config?:    ModelConfig
}

InferenceResponse {
  modelId:    ModelId
  output:     ModelOutput    // model-specific
  runtime:    'browser-onnx' | 'python-gpu'
  inferenceTimeMs: number
  modelVersion: string
}
```

### 6.3 Browser ONNX runtime

- **Models stored as `.onnx` files** in Supabase Storage, downloaded on demand, cached in IndexedDB.
- **Inference via `onnxruntime-web`** with WebGPU backend where available, WASM fallback.
- **Model registry**: a manifest of available browser-runnable models with their input/output schemas.
- **Versioning**: models have versions; the registry pins a version per environment.

### 6.4 Python GPU runtime

- **PyTorch** for LSTM and Transformer (loaded once, kept warm).
- **XGBoost/CatBoost/LightGBM** with GPU support.
- **TabPFN** for in-context tabular inference.
- **Inference server**: FastAPI endpoint `/ai/infer` accepts `InferenceRequest`, routes to the right model, returns `InferenceResponse`.
- **Model warmup**: models loaded at backend startup, kept in GPU memory.
- **Batching**: requests batched per model for throughput.

---

## 7. Backend Architecture (Python)

### 7.1 Service layout

```
python-backend/
├─ main.py                          # FastAPI app entry
├─ api/                             # HTTP routers
│  ├─ market_data.py                # GET /market/quote, /market/level2, /market/providers
│  ├─ ta.py                         # GET /ta/indicators, /ta/signal, /ta/levels
│  ├─ options.py                    # GET /options/chain, /options/iv, /options/unusual
│  ├─ news.py                       # GET /news/feed, /news/sentiment, /news/entities
│  ├─ macro.py                      # GET /macro/indicators, /macro/yield-curve
│  ├─ forecast.py                   # POST /forecast/run, GET /forecast/result
│  ├─ probability.py                # POST /probability/simulate
│  ├─ validator.py                  # POST /validator/backtest, GET /validator/result
│  ├─ report.py                     # POST /report/generate, GET /report/{id}
│  └─ ws.py                         # WebSocket /ws/events (bus bridge)
├─ services/                        # Business logic
│  ├─ market_data/
│  │  ├─ adapters/
│  │  │  ├─ base.py                 # MarketDataProvider interface
│  │  │  ├─ yahoo.py
│  │  │  ├─ finnhub.py
│  │  │  ├─ polygon.py
│  │  │  ├─ flashalpha.py
│  │  │  ├─ fred.py
│  │  │  ├─ alphavantage.py
│  │  │  └─ simulated.py            # DEV ONLY — never used in production
│  │  ├─ aggregator.py              # failover chain: yahoo → finnhub → polygon → flashalpha → fred → alphavantage
│  │  ├─ cache.py                   # Redis cache
│  │  └─ ws_server.py               # broadcast quotes to frontend
│  ├─ ta_engine/                    # pandas-ta wrapper
│  ├─ options_engine/               # Black-Scholes, IV solver
│  ├─ news_engine/                  # HuggingFace FinBERT
│  ├─ macro_engine/                 # FRED + international sources
│  ├─ forecast_engine/              # orchestrates AI models
│  ├─ probability_engine/           # Monte Carlo
│  ├─ validator_engine/             # vectorbt real backtesting
│  ├─ report_engine/                # markdown → json → pdf
│  └─ ai_router/                    # routes inference to ONNX/Python
├─ inference/                       # AI model loaders
│  ├─ onnx_runtime.py
│  ├─ lstm.py
│  ├─ transformer.py
│  ├─ tabpfn.py
│  ├─ xgboost_model.py
│  ├─ catboost_model.py
│  └─ lightgbm_model.py
├─ backtest/                        # vectorbt wrappers
│  ├─ engine.py
│  ├─ strategies/
│  │  ├─ athena_ensemble.py
│  │  ├─ ta_only.py
│  │  ├─ news_only.py
│  │  ├─ options_only.py
│  │  ├─ macro_only.py
│  │  └─ forecast_only.py
│  └─ metrics.py                    # Sharpe, Sortino, MaxDD, Calmar, win rate
├─ bus/                             # Message bus
│  ├─ events.py                     # Pydantic event models (generated from OpenAPI)
│  ├─ redis_pubsub.py               # Redis Pub/Sub transport
│  ├─ nats_transport.py             # NATS transport (alternative)
│  └─ client.py                     # BusClient (publish + subscribe)
├─ agents/                          # Long-running backend agents
│  ├─ market_data_agent.py          # always-on ingestion
│  ├─ ta_agent.py                   # computes indicators for watchlist
│  ├─ news_agent.py                 # ingests news
│  ├─ options_agent.py              # refreshes chains
│  ├─ macro_agent.py                # ingests macro
│  ├─ forecast_agent.py             # runs forecasts on schedule
│  ├─ probability_agent.py          # on-demand simulations
│  └─ validator_agent.py            # nightly backtests
├─ db/                              # Supabase client + repositories
│  ├─ supabase_client.py
│  ├─ workspaces.py
│  ├─ reports.py
│  ├─ backtests.py
│  └─ models.py
├─ models/                          # Pydantic models (shared with frontend)
├─ config/                          # Settings
│  ├─ settings.py                   # Pydantic Settings (env vars)
│  └─ providers.yaml                # provider credentials + endpoints
├─ tests/
│  ├─ unit/
│  ├─ integration/
│  └─ e2e/
├─ pyproject.toml
├─ Dockerfile
└─ README.md
```

### 7.2 Backend agent lifecycle

- Agents are **asyncio tasks** managed by a supervisor.
- Supervisor restarts crashed agents with exponential backoff.
- Agents subscribe to bus events at startup.
- Agents publish events as they complete work.
- Agents expose health via `/health/agents` endpoint.

### 7.3 Real backtesting pipeline (Self Validation)

```
1. User triggers backtest via UI → POST /validator/backtest
2. ValidatorEngine receives request:
   a. Load historical data for symbol(s) via market_data service
   b. Load strategy implementation (e.g., athena_ensemble.py)
   c. Run vectorbt backtest:
      - For each bar:
        - Compute features (TA + news + options + macro + AI forecast)
        - Strategy emits signal: long / short / flat
        - Execute at next bar open
        - Record trade
      - Compute metrics: returns, Sharpe, Sortino, MaxDD, Calmar, win rate
   d. Store result in Supabase (backtests table)
   e. Publish validator:backtest-run event
3. Frontend VAL module subscribes to event, renders equity curve + trade history
```

**Never mocked.** If historical data is unavailable, the backtest fails with a clear error. If a model fails to infer, the bar is skipped and recorded as a gap.

---

## 8. Supabase Schema

```
auth.users                    # Supabase Auth (per-user)

workspaces
  id              uuid PK
  user_id         uuid FK → auth.users
  name            text
  main_indicator  text CHECK (in ('ES','SPY'))
  panel_layout    jsonb
  background_services jsonb
  settings        jsonb
  created_at      timestamptz
  updated_at      timestamptz
  -- RLS: user_id = auth.uid()

watchlists
  id              uuid PK
  workspace_id    uuid FK → workspaces
  symbol          text
  asset_class     text
  position        int
  -- RLS: workspace.user_id = auth.uid()

module_instances               # persisted panel instances
  id              uuid PK
  workspace_id    uuid FK → workspaces
  module_id       text
  config          jsonb
  state           jsonb
  created_at      timestamptz
  -- RLS: workspace.user_id = auth.uid()

reports
  id              uuid PK
  user_id         uuid FK → auth.users
  symbol          text
  title           text
  audience        text
  timeframe       text
  sections        jsonb
  markdown        text          # canonical
  json_content    jsonb         # structured
  pdf_path        text          # Supabase Storage path
  status          text          # 'generating' | 'completed' | 'failed'
  created_at      timestamptz
  -- RLS: user_id = auth.uid()

backtests
  id              uuid PK
  user_id         uuid FK → auth.users
  strategy_id     text
  symbol          text
  config          jsonb
  equity_curve    jsonb
  trade_history   jsonb
  metrics         jsonb         # { returns, sharpe, sortino, max_dd, calmar, win_rate, ... }
  calibration     jsonb
  started_at      timestamptz
  completed_at    timestamptz
  status          text
  -- RLS: user_id = auth.uid()

agent_runs                     # audit log for backend agents
  id              uuid PK
  agent_id        text
  module_id       text
  started_at      timestamptz
  completed_at    timestamptz
  status          text
  error           text
  metrics         jsonb
  -- RLS: service role only (not directly user-readable)

model_artifacts                # AI model registry
  id              uuid PK
  model_id        text         # 'lstm', 'transformer', etc.
  version         text
  runtime         text         # 'python-gpu' | 'browser-onnx'
  storage_path    text         # Supabase Storage path
  input_schema    jsonb
  output_schema   jsonb
  created_at      timestamptz
  -- RLS: public read (model listing); service role write

storage:
  reports/                      # PDF reports
  models/                       # ONNX models for browser
  exports/                      # user-exported artifacts
```

---

## 9. Frontend Architecture (Next.js)

### 9.1 Top-level layout

```
nextjs-dashboard/
├─ app/                                # Next.js app-router (THIN shell)
│  ├─ layout.tsx                       # <html class="dark">, fonts, providers
│  ├─ page.tsx                         # redirect to /workspace/{default}
│  ├─ auth/
│  │  ├─ login/page.tsx
│  │  └─ callback/route.ts            # OAuth callback
│  ├─ workspace/
│  │  └─ [workspaceId]/
│  │     ├─ layout.tsx                # <WorkspaceShell>
│  │     └─ page.tsx                  # renders <WorkspaceCanvas/>
│  └─ api/                            # BFF (proxy to Python backend)
│     └─ [...path]/route.ts
├─ modules/                            # one package per module (see §10)
│  ├─ dashboard/
│  ├─ live-market/
│  ├─ technical-analysis/
│  ├─ news-intelligence/
│  ├─ options-intelligence/
│  ├─ macro-intelligence/
│  ├─ ai-forecast/
│  ├─ probability-engine/
│  ├─ report-generator/
│  └─ self-validation/
├─ lib/                                # shared infrastructure (see §9.2)
├─ public/
├─ next.config.ts                      # Turbopack, transpile ONNX
├─ tailwind.config.ts                  # v4, dark-only
├─ tsconfig.json                       # strict, path aliases
├─ package.json
├─ vitest.config.ts
├─ playwright.config.ts
└─ README.md
```

### 9.2 Shared infrastructure (`lib/`)

```
lib/
├─ event-bus/                          # central nervous system
│  ├─ types.ts                         # all event types (discriminated union)
│  ├─ bus.ts                           # in-process pub/sub
│  ├─ websocket-bridge.ts              # mirrors backend events
│  ├─ patterns.ts                      # event pattern matching
│  └─ index.ts                         # public façade
├─ module-registry/                    # Bloomberg-style module catalog
│  ├─ contract.ts                      # ModuleManifest, ModuleInstance interfaces
│  ├─ registry.ts                      # registers all 10 modules at boot
│  ├─ loader.ts                        # lazy-loads module bundles
│  └─ index.ts
├─ workspace/                          # workspace state (Zustand)
│  ├─ store.ts                         # panels, instances, layout
│  ├─ persist.ts                       # Supabase sync via TanStack Query
│  ├─ undo-redo.ts                     # zundo middleware
│  ├─ main-indicator.ts                # ES/SPY switchable
│  └─ index.ts
├─ module-instance/                    # per-instance state
│  ├─ store.ts                         # Zustand slice per instanceId
│  └─ index.ts
├─ market-data/                        # frontend cache layer
│  ├─ client.ts                        # talks to Python backend
│  ├─ hooks.ts                         # useQuote, useLevel2 (TanStack Query)
│  ├─ cache.ts                         # query keys, stale times
│  └─ index.ts
├─ ai-runtime/                         # ONNX Runtime Web
│  ├─ onnx-loader.ts                   # loads .onnx from Supabase Storage
│  ├─ onnx-session.ts                  # session pool
│  ├─ router.ts                        # browser-onnx vs python-gpu decision
│  ├─ model-registry.ts                # available browser models
│  └─ index.ts
├─ supabase/                           # Supabase client + types
│  ├─ client.ts                        # browser client
│  ├─ server.ts                        # server client (RSC)
│  ├─ types.ts                         # generated DB types
│  └─ index.ts
├─ auth/                               # Supabase Auth wrapper
│  ├─ provider.tsx                     # AuthProvider
│  ├─ hooks.ts                         # useUser, useSession
│  ├─ guards.ts                        # withAuth, withWorkspace
│  └─ index.ts
├─ di/                                 # dependency injection
│  ├─ container.ts                     # lightweight DI container
│  ├─ tokens.ts                        # injection tokens
│  └─ index.ts
├─ config/                             # env + app config
│  ├─ env.ts                           # Zod-validated env vars
│  ├─ providers.ts                     # provider config
│  ├─ models.ts                        # AI model config
│  └─ index.ts
├─ logger/                             # structured logger
│  ├─ logger.ts                        # Pino browser logger
│  ├─ transport.ts                     # sends to backend
│  └─ index.ts
├─ keyboard/                           # Bloomberg-style shortcuts
│  ├─ shortcuts.ts                     # global shortcut registry
│  ├─ palette.ts                       # cmdk command palette
│  └─ index.ts
├─ ui/                                 # shadcn/ui primitives + Panel system
│  ├─ panel/                           # Bloomberg-style panel chrome
│  │  ├─ panel.tsx                     # PanelShell (header, body, footer, chrome)
│  │  ├─ panel-header.tsx              # title, instance config, controls
│  │  ├─ panel-controls.tsx            # move, resize, minimize, close, config
│  │  └─ index.ts
│  ├─ command-palette/                 # cmdk-based launcher
│  ├─ ticker-tape/                     # animated ticker
│  ├─ sidebar/                         # modules + watchlist + status
│  ├─ topbar/                          # ticker + title + search + status
│  ├─ status-banner/                   # active symbol + widgets count
│  ├─ data-display/                    # StatCard, KpiTile, Gauge, Heatmap
│  ├─ tables/                          # DataTable with sort/filter/virtualization
│  ├─ charts/                          # Recharts wrappers (typed, themed)
│  ├─ forms/                           # form controls with Zod validation
│  ├─ overlays/                        # Dialog, Drawer, Sheet, Popover
│  ├─ feedback/                        # Skeleton, Error, Empty, Toast
│  └─ index.ts
├─ utils/                              # pure utilities
│  ├─ format.ts                        # number, currency, percent, time
│  ├─ math.ts                          # financial math
│  ├─ time.ts                          # time helpers
│  └─ index.ts
└─ types/                              # shared types (cross-module)
   ├─ domain.ts                        # Symbol, AssetClass, Timeframe, etc.
   ├─ events.ts                        # re-export from event-bus
   └─ index.ts
```

### 9.3 Routing strategy

The app-router is **thin** — it does almost nothing. The route `workspace/[id]` mounts `<WorkspaceShell>` which:
1. Loads the workspace record from Supabase
2. Initializes the workspace Zustand store
3. Renders the panel grid
4. For each panel, lazy-loads the corresponding module bundle and mounts the instance

URL changes when the user switches workspaces. URL does NOT change when the user opens/closes/moves panels (that's workspace-internal state, persisted separately).

---

## 10. Per-Module Package Structure (canonical)

Every one of the 10 modules follows this exact structure. No exceptions.

```
modules/<module-name>/
├─ README.md                # What it does, public API, events, dependencies
├─ manifest.ts              # ModuleManifest (id, shortcut, capabilities, etc.)
├─ config.ts                # Zod schema for instance config + defaults
├─ types.ts                 # All types this module exports (DTOs, state, etc.)
├─ api.ts                   # Backend API client (typed, via lib/supabase or fetch)
├─ hooks.ts                 # TanStack Query hooks + Zustand selectors
├─ components/              # UI components (scoped to this module)
│  ├─ <module>-panel.tsx    # the panel component (renders inside PanelShell)
│  ├─ <module>-header.tsx   # instance config UI (symbol picker, timeframe, etc.)
│  ├─ <module>-footer.tsx   # status footer (last update, source, latency)
│  └─ ...                   # sub-components (charts, tables, etc.)
├─ services/                # business logic (pure functions, no React)
│  ├─ <service>.ts          # e.g., computeIndicators, parseChain, etc.
│  └─ ...
├─ agents/                  # headless agent (optional, only if capabilities.headless)
│  └─ <module>-agent.ts     # subscribes to events, publishes events
├─ tests/                   # tests
│  ├─ services.test.ts      # unit tests for services
│  ├─ components.test.tsx   # component tests
│  ├─ agent.test.ts         # agent tests (if applicable)
│  └─ integration.test.ts   # end-to-end module tests
└─ index.ts                 # PUBLIC FAÇADE — only this is importable outside
```

### 10.1 README.md (template)

Each module README contains:
- One-paragraph purpose
- Bloomberg shortcut
- Capabilities (launchable / multi-instance / headless)
- Public API reference (queries + commands + events)
- Event subscriptions + publications
- Dependencies (which other modules' APIs it consumes, if any)
- Configuration options
- Test instructions

### 10.2 manifest.ts (example shape for Technical Analysis)

```typescript
// modules/technical-analysis/manifest.ts
export const technicalAnalysisManifest: ModuleManifest = {
  id: 'technical-analysis',
  name: 'Technical Analysis',
  shortcut: 'TA',
  description: 'Real-time indicator computation and signal generation',
  icon: ChartCandlestickIcon,
  version: '1.0.0',
  capabilities: {
    launchable: true,
    multiInstance: true,
    headless: true,
    defaultHotkey: 'g t',
  },
  configSchema: taConfigSchema,
  instanceStateSchema: taStateSchema,
  subscriptions: [
    'market:quote-updated',
    'ui:symbol-selected',
    'ui:timeframe-changed',
  ],
  publications: [
    'ta:indicator-computed',
    'ta:signal-emitted',
    'ta:level-identified',
  ],
  publicAPI: taPublicAPI,
  panelComponent: TAPanel,
  agentFactory: createTAAgent,
};
```

### 10.3 Dependency rules (enforced by ESLint)

```
┌─────────────────────────────────────────────────────┐
│  modules/<m>/                                        │
│    components  →  hooks  →  services  →  api  →  types
│                                ↓                     │
│                          event-bus (cross-module)    │
│                                ↓                     │
│                  other modules' PUBLIC FAÇADES only  │
└─────────────────────────────────────────────────────┘
```

**Enforced via** `eslint-plugin-import` + `import/no-boundaries` + custom rule:
- `components/` may import from `hooks/`, `services/`, `types/`, `lib/ui`, `lib/event-bus`.
- `hooks/` may import from `services/`, `api/`, `types/`, `lib/event-bus`, `lib/market-data`, `lib/supabase`, `lib/ai-runtime`.
- `services/` may import from `api/`, `types/`, `lib/utils`, `lib/event-bus`.
- `api/` may import from `types/`, `lib/supabase`, `lib/config`.
- `agents/` may import from `services/`, `api/`, `types/`, `lib/event-bus`.
- **NO** module may import from another module's internal files. Only `modules/<other>/index.ts` is allowed.
- **NO** module may import from `app/` (the Next.js shell). The shell imports modules, never the reverse.

### 10.4 Public façade (`index.ts`)

```typescript
// modules/technical-analysis/index.ts
export { technicalAnalysisManifest } from './manifest';
export type { TAConfig, TAState, TAIndicator, TASignal } from './types';
export { taPublicAPI } from './api';
export { TAPanel } from './components/ta-panel';
export { useTAIndicators, useTASignal } from './hooks';
// INTERNAL FILES (components/, services/, agents/) ARE NOT EXPORTED.
// Other modules use taPublicAPI.queries.getIndicators(...) — they never
// reach into the internals.
```

---

## 11. Workspace Shell (the Bloomberg-style chrome)

The shell is the only place that knows about the **module system**. Modules themselves don't know about the shell.

```
<WorkspaceShell>
├─ <Sidebar>                          ← Modules nav + Watchlist + Status
│  ├─ <Brand>                         ATHENA-X logo + "v3.x"
│  ├─ <NavSection title="Modules">    10× <NavButton> (click launches in active panel)
│  ├─ <NavSection title="Watchlist">  symbols list, click → ui:symbol-selected
│  └─ <SidebarFooter>                 "Engine online · v3.x"
├─ <Topbar>
│  ├─ <TickerTape>                    animated, derived from watchlist (top 12)
│  ├─ <ModuleTitle>                   active workspace name + main indicator
│  ├─ <SymbolSearch>                  cmdk palette trigger
│  ├─ <MainIndicatorSwitch>           ES ⇄ SPY (the switchable main indicator)
│  ├─ <MarketStatus>                  clock + "Live"
│  ├─ <BellButton>                    notifications drawer
│  └─ <SettingsButton>                settings dialog
├─ <CommandPalette>                   Ctrl+K — launch modules, switch symbols
├─ <WorkspaceCanvas>                  react-grid-layout
│  └─ for each panel:
│     └─ <PanelShell>
│        ├─ <PanelHeader>             title + instance config + controls
│        ├─ <PanelBody>
│        │  └─ <ModulePanel>          lazy-loaded from module bundle
│        └─ <PanelFooter>             status (last update, source)
├─ <NotificationsDrawer>              sonner history + backend alerts
├─ <SettingsDialog>                   workspace settings, refresh rates, providers
└─ <Toaster />                        sonner
```

### 11.1 Panel chrome (Bloomberg-style)

Every panel has:
- **Title bar**: module icon + name + instance config summary (e.g., "TA — NVDA · 5m") + controls
- **Controls**: move, resize, minimize, maximize, detach (pop-out), configure, close
- **Body**: the module's panel component
- **Footer**: last update timestamp + data source + latency
- **Drag handle**: title bar (for reordering in the grid)
- **Resize handle**: bottom-right corner

### 11.2 Multi-instance UI

When a module is multi-instance, the user can launch it again — it opens in a new panel with default config. Each panel has its own:
- Instance ID (UUID)
- Symbol/timeframe config
- Zustand slice
- TanStack Query cache namespace
- Event subscriptions (filtered by instance config)

### 11.3 Command palette (Ctrl+K)

The palette is the Bloomberg-style launcher:
- Type `TA NVDA` → opens TA panel for NVDA
- Type `NEWS` → opens News panel
- Type `ES` or `SPY` → switches main indicator
- Type `RPT AAPL IC 30d` → generates AAPL report for Investment Committee, 30-day horizon
- Type `VAL Ensemble NVDA` → runs backtest

---

## 12. AI Routing Implementation

### 12.1 Router decision flow

```
InferenceRequest arrives
        │
        ▼
   ┌────────────────┐
   │  Check modelId │
   └────────┬───────┘
            │
   ┌────────┴───────────────────────────────────────┐
   │                                                │
   ▼                                                ▼
┌──────────────┐                          ┌────────────────────┐
│ Browser-OK?  │                          │  Python-required?  │
│ (lookup tbl) │                          │  (lookup table)    │
└──────┬───────┘                          └─────────┬──────────┘
       │                                            │
       ▼                                            ▼
┌──────────────┐                          ┌────────────────────┐
│ ONNX Runtime │                          │  POST /ai/infer    │
│ Web (WebGPU) │                          │  → Python GPU      │
└──────────────┘                          └────────────────────┘
       │                                            │
       └──────────────┬─────────────────────────────┘
                      ▼
              InferenceResponse
              (with runtime field for transparency)
```

### 12.2 Routing table (single source of truth)

```typescript
// lib/ai-runtime/router.ts
const AI_ROUTING_TABLE: Record<ModelId, AIRuntime> = {
  'lstm':              'python-gpu',     // NEVER browser
  'transformer':       'python-gpu',     // NEVER browser
  'tabpfn':            'python-gpu',
  'xgboost':           'python-gpu',
  'catboost':          'python-gpu',
  'lightgbm-large':    'python-gpu',
  'lightgbm-small':    'browser-onnx',
  'random-forest':     'browser-onnx',
  'logistic':          'browser-onnx',
};
```

This table is **non-overridable at runtime**. The router throws if a model is not in the table.

### 12.3 Forecast ensemble composition

The Forecast Engine composes an ensemble from multiple models. The ensemble itself is configured per workspace:

```
ForecastEnsemble {
  models: [
    { id: 'lstm',           weight: 0.20, runtime: 'python-gpu' },
    { id: 'transformer',    weight: 0.25, runtime: 'python-gpu' },
    { id: 'tabpfn',         weight: 0.15, runtime: 'python-gpu' },
    { id: 'xgboost',        weight: 0.15, runtime: 'python-gpu' },
    { id: 'catboost',       weight: 0.10, runtime: 'python-gpu' },
    { id: 'lightgbm-small', weight: 0.10, runtime: 'browser-onnx' },
    { id: 'random-forest',  weight: 0.05, runtime: 'browser-onnx' },
  ]
}
```

Inference runs in parallel across models. Results aggregated by weight. The ensemble composition is editable in the Forecast module's instance config.

---

## 13. Report Generation Pipeline

Per requirement #5: markdown → json → pdf → store at database → dashboard.

```
1. User triggers report generation
   ↓
2. Report Engine (Python) receives request:
   a. Compose report config: symbol, audience, timeframe, sections
   b. For each section, query the relevant module's public API:
      - Executive Summary: forecast + probability + validator
      - Market Snapshot: live-market
      - Technical Analysis: ta
      - News & Sentiment: news
      - Options Intelligence: options
      - Macro Context: macro
      - AI Forecast: forecast
      - Risk Assessment: probability + validator
      - Final Recommendation: forecast + probability + validator
   c. Generate Markdown (canonical format):
      - Section templates with Jinja2
      - Tables, charts (rendered as PNG, embedded as base64)
      - Audience-specific tone (Investment Committee vs Trader)
   d. Generate JSON (structured):
      - Same content as Markdown, but as a typed JSON document
      - Schema versioned
   e. Generate PDF:
      - WeasyPrint or ReportLab
      - Institutional dark theme (matches dashboard)
      - Cover page, TOC, sections, appendix
   f. Upload PDF to Supabase Storage: reports/{userId}/{reportId}.pdf
   g. Insert report record into reports table (markdown, json, pdf_path)
   h. Publish report:generation-completed event
   ↓
3. Frontend Report Generator module:
   - Subscribes to event
   - Updates report list
   - Shows preview (markdown rendered), with "View PDF" / "Export" buttons
   - "Export" downloads PDF or JSON
```

---

## 14. Backtesting Pipeline (Real, Never Mock)

Per requirement #6: real Python backtesting.

### 14.1 Backtest request flow

```
1. User selects strategy + symbol in VAL module
   ↓
2. POST /validator/backtest
   { strategy_id: 'athena-ensemble', symbol: 'NVDA', config: {...} }
   ↓
3. ValidatorEngine receives request:
   a. Load strategy implementation: backtest/strategies/athena_ensemble.py
   b. Load historical data via market_data service:
      - Daily bars for NVDA, 2 years back
      - News sentiment history
      - Options IV history
      - Macro indicators history
   c. Run vectorbt backtest:
      - For each trading day:
        - Compute features:
          - TA indicators (pandas-ta)
          - News sentiment (FinBERT)
          - Options IV (Black-Scholes)
          - Macro indicators
          - AI forecast (if strategy includes AI)
        - Strategy.emit_signal(features) → { direction, size, stop, target }
        - Execute at next day open (slippage modeled)
        - Record trade with entry/exit/prices/PNL/R-multiple
      - Compute metrics:
        - Total return, CAGR
        - Sharpe ratio, Sortino ratio
        - Max drawdown, Calmar ratio
        - Win rate, profit factor
        - Average R-multiple
      - Compute probability calibration:
        - Bucket forecast probabilities by decile
        - Compare to actual outcome rates
   d. Store results in Supabase backtests table
   e. Publish validator:backtest-run event with full results
   ↓
4. Frontend VAL module:
   - Subscribes to event
   - Renders equity curve, drawdown, trade history, metrics, calibration
   - All numbers are REAL — no mock data anywhere
```

### 14.2 Strategy implementations

Each strategy is a Python class implementing a common interface:

```python
class Strategy(Protocol):
    def emit_signal(self, features: Features) -> Signal: ...
```

Strategies:
- `ATHENA-X Ensemble` — combines all 6 module signals (TA + News + Options + Macro + Forecast + Probability)
- `TA Only` — uses only TA signals
- `News Only` — uses only news sentiment
- `Options Only` — uses only options flow
- `Macro Only` — uses only macro indicators
- `AI Forecast Only` — uses only forecast ensemble

---

## 15. Cross-Cutting Concerns

### 15.1 Configuration management

- **Frontend env**: `NEXT_PUBLIC_*` vars validated by Zod at boot.
- **Backend env**: Pydantic Settings, loaded from `.env` + secrets manager.
- **Per-module config**: each module's `config.ts` exports a Zod schema. Instance configs are validated against this schema before instantiation.
- **No hardcoded values**: symbols, intervals, colors, model paths, provider URLs — all in config.

### 15.2 Logging

- **Frontend**: Pino browser logger, batched, sent to backend `/logs` endpoint.
- **Backend**: Pino server logger, structured JSON, sent to stdout (container-logging compatible).
- **Correlation**: every bus event carries `eventId`, `correlationId`, `causationId` for tracing.

### 15.3 Observability

- **Frontend errors**: Sentry browser SDK.
- **Backend errors**: Sentry Python SDK.
- **Metrics**: backend exposes `/metrics` (Prometheus format) for agent health, bus throughput, inference latency.
- **Tracing**: OpenTelemetry on backend (FastAPI instrumentation + bus instrumentation).

### 15.4 Testing strategy

| Layer | Tool | Scope |
|---|---|---|
| Pure functions (services/) | Vitest | unit |
| React components | Vitest + Testing Library | component |
| Event bus interactions | Vitest + MSW | integration |
| Module-level e2e | Vitest + Playwright | module |
| Backend unit | pytest | unit |
| Backend integration | pytest + httpx | integration |
| Backend e2e | pytest + testcontainers | e2e |
| Full system e2e | Playwright | cross-module |

Each module MUST ship with:
- ≥80% line coverage on `services/`
- ≥1 component test per `components/` file
- ≥1 integration test exercising the full module (mount → subscribe → publish → unmount)
- ≥1 agent test (if the module has `agents/`)

### 15.5 CI/CD gates (per module)

Every PR that touches a module MUST pass:
1. `tsc --noEmit` (TypeScript strict, no errors)
2. `next lint` (ESLint, including import-boundary rules)
3. `vitest run` (all tests pass)
4. `vitest run --coverage` (≥80% on services/)
5. Build succeeds (`next build`)
6. Bundle size within budget (per-module lazy chunks ≤200KB gzipped)

If any gate fails, the PR is blocked. No exceptions.

---

## 16. Monorepo Structure (STEP 3 preview)

```
athena-x/                                 ← monorepo root
├─ apps/
│  ├─ nextjs-dashboard/                   ← Next.js 16 frontend
│  └─ python-backend/                     ← FastAPI Python backend
├─ packages/                              ← shared packages
│  ├─ event-schema/                       ← OpenAPI spec → TS + Pydantic generators
│  │  ├─ schema.yaml                      ← single source of truth for events
│  │  ├─ generate-ts.ts                   ← generates lib/event-bus/types.ts
│  │  ├─ generate-py.py                   ← generates backend/bus/events.py
│  │  └─ README.md
│  ├─ ui-kit/                             ← shared shadcn/ui components
│  └─ eslint-config/                      ← shared ESLint config (with import boundaries)
├─ infrastructure/
│  ├─ supabase/                           ← migrations + RLS policies
│  │  ├─ migrations/
│  │  └─ seed.sql
│  ├─ docker-compose.yml                  ← local dev (Postgres + Redis + NATS)
│  └─ terraform/                          ← production infra (optional)
├─ .github/
│  └─ workflows/
│     ├─ ci-frontend.yml
│     ├─ ci-backend.yml
│     └─ deploy.yml
├─ docs/
│  ├─ architecture/                       ← this document + diagrams
│  ├─ modules/                            ← per-module deep dives (generated in STEP 4)
│  └─ runbooks/
├─ package.json                           ← pnpm workspace root
├─ pnpm-workspace.yaml
├─ turbo.json                             ← Turborepo (build orchestration)
├─ .eslintrc.root.js
├─ .gitignore
└─ README.md
```

---

## 17. Migration from STEP 1 → STEP 2 (what changes)

| STEP 1 (current) | STEP 2 (redesign) |
|---|---|
| `activeModule` state switches pages | Workspace hosts N panel instances concurrently |
| 1 URL per "view" (none, actually — single page) | 1 URL per workspace; panels are workspace state |
| Mock data per module | Real data via Python backend provider chain |
| 10 `setInterval` timers | 1 backend ingestion agent + bus events |
| Cross-Module Signals is hardcoded | Cross-Module Signals is a real subscriber to all 6 agent event streams |
| No agents | 7 backend agents + browser agents (where applicable) |
| LSTM is a label | LSTM is a real PyTorch model on GPU |
| Backtest is mock trade history | Backtest is real vectorbt run over historical data |
| Reports are not generated | Reports: markdown → json → pdf → Supabase → dashboard |
| Forced dark, no toggle | Dark-only (institutional) — no toggle by design |
| No persistence | Supabase: workspaces, watchlists, reports, backtests, agent runs |
| Monolithic files | Modular packages with façades + ESLint boundaries |
| Bell/Settings/Search are dead | All wired: notifications drawer, settings dialog, command palette |
| No keyboard shortcuts | Bloomberg-style `g t` / `g n` / Ctrl+K palette |
| `<PanelChrome>` on 2 modules | Panel chrome on ALL modules |
| Single TA instance | Multi-instance TA (NVDA + AAPL simultaneously) |
| No main indicator switch | ES ⇄ SPY switchable at workspace level |

---

## 18. STEP 2 Deliverable Summary

This document specifies:

1. ✅ The 10 modules reframed as Bloomberg-style launchable units with shortcuts, capabilities, and event contracts
2. ✅ The module contract (manifest + instance + public API + agent)
3. ✅ The workspace model (panels, multi-instance, persistence)
4. ✅ The message bus topology + complete event taxonomy
5. ✅ The hybrid AI runtime with explicit, non-overridable routing table
6. ✅ The Python backend architecture (services, agents, inference, backtest)
7. ✅ The Supabase schema (per-user, workspace-aware, RLS)
8. ✅ The Next.js frontend architecture (thin shell + 10 module packages)
9. ✅ The canonical per-module structure (README + manifest + config + types + api + hooks + components + services + agents + tests + index.ts)
10. ✅ The dependency rules enforced by ESLint (no circular, no internal imports)
11. ✅ The report generation pipeline (markdown → json → pdf → storage → dashboard)
12. ✅ The real backtesting pipeline (vectorbt, never mock)
13. ✅ The switchable main indicator (ES ⇄ SPY)
14. ✅ The provider chain (Yahoo → Finnhub → Polygon → FlashAlpha → FRED → AlphaVantage)
15. ✅ The CI/CD gates (tsc + lint + tests + coverage + build, per module)
16. ✅ The monorepo structure for STEP 3

### What STEP 3 will produce

A complete folder skeleton for the entire monorepo, with:
- All package directories created
- All `package.json` / `pyproject.toml` / config files written
- All `index.ts` / `manifest.ts` / `README.md` stubs written (with content, not placeholders)
- All shared infrastructure (`lib/`) stubbed
- All module packages stubbed with the canonical structure
- All test infrastructure (vitest, pytest, playwright) configured
- All CI workflows written
- **No feature implementation** — that's STEP 4, one module at a time

### What STEP 4 will produce (per module, in order)

1. `lib/event-bus/` + `packages/event-schema/` (foundation — must exist before any module)
2. `lib/supabase/` + `lib/auth/` (foundation)
3. `lib/module-registry/` + `lib/workspace/` (foundation)
4. `modules/live-market/` (data source — other modules depend on it)
5. `modules/technical-analysis/` (depends on live-market)
6. `modules/news-intelligence/`
7. `modules/options-intelligence/`
8. `modules/macro-intelligence/`
9. `modules/ai-forecast/` (depends on all 4 above)
10. `modules/probability-engine/` (depends on forecast + options)
11. `modules/self-validation/` (depends on forecast + probability)
12. `modules/report-generator/` (depends on all)
13. `modules/dashboard/` (depends on all)
14. Python backend services (mirrors the above order)
15. Polish: keyboard shortcuts, command palette, animations, error states

After each module: `tsc --noEmit` + `next lint` + `vitest run` + `next build`. Zero errors before proceeding.

---

**Approval gate**: please confirm this design before I proceed to STEP 3 (folder skeleton).
