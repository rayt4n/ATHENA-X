# ATHENA-X — Reverse-Engineering & Architecture Audit (STEP 1)

> Source site: `https://u1eym5e6d210-d.space-z.ai/`
> Detected product name: **ATHENA-X v3.2.1 — Quantitative Intelligence Terminal**
> Analysis method: live browser traversal (DOM walk, accessibility tree per screen, network inspection, JS-bundle inspection, CSS-token extraction)
> **No code is written in this step. This document is the deliverable for STEP 1 and the input for STEP 2.**

---

## 0. Executive Summary

ATHENA-X is a **single-page, client-rendered quantitative market intelligence terminal** built on **Next.js 16.1.3 (Turbopack, app-router, RSC)**, **React 19**, **Tailwind CSS v4 (OKLCH color tokens)**, **shadcn/ui primitives**, **lucide-react icons**, **sonner** (toast), and **recharts** (charting).

The product exposes **10 modules** behind a fixed shell (left sidebar + top header + main canvas), each module is a single large client component that hard-codes its own simulated dataset. State is local, not shared. There is **no backend, no Supabase, no TanStack Query, no Zustand, no event bus, no real AI agents** — every "live" number on screen is produced by deterministic mock generators in the client bundle. The "AI agents" referenced in the brief do not currently exist as runtime entities; the modules that *imply* agents (Cross-Module Signals, AI Forecast Engine, Probability Engine, Self Validation) are static UIs.

The product is visually polished, conceptually coherent, and **architecturally a prototype**. The rebuild target (modular, scalable, event-driven, agent-bus-driven, Supabase-backed, Zustand+TanStack Query) is therefore a **clean-slate rewrite**, not a refactor.

| Dimension | Current state | Target state (ATHENA-X rebuild) |
|---|---|---|
| Stack | Next.js 16, React 19, Tailwind v4, shadcn/ui, lucide, sonner, recharts | + Zustand, TanStack Query, Supabase, Framer Motion (per brief) |
| Rendering | CSR with RSC shell | RSC + selective CSR (data-heavy widgets) |
| Data | 100% client-side mock | Supabase tables + edge functions + provider adapters |
| State | Local `useState` per module | Zustand stores + TanStack Query cache |
| Cross-module comms | None (hardcoded) | Central event bus (typed pub/sub) |
| Agents | None | N agent workers communicating through the bus |
| Persistence | None | Supabase (user prefs, watchlists, reports, backtests) |
| Testing | None | Vitest + Playwright per module |
| Modularity | Monolithic page-per-module | Feature-sliced module packages with public façade |

---

## 1. Detected Stack (forensic evidence)

Captured from the live site:

| Layer | Evidence |
|---|---|
| Framework | Next.js `16.1.3` (`window.next.version`) |
| Bundler | Turbopack (`turbopack-b25efb3e5da9efbd.js`, `globalThis.TURBOPACK` markers) |
| Rendering | RSC + app-router (`self.__next_f.push` flight payload, `next-route-announcer`) |
| React | 19 (transitional element symbol, `useFormState`, `useActionState`, `useOptimistic` markers) |
| Styling | Tailwind CSS v4 (`--background`, `--foreground`, `--card`, `--muted`, `--primary`, `--border`, `--sidebar`, `--pos`, `--neg`, `--accent`, `--chart` all in `lab()`/`oklch()`) |
| UI primitives | shadcn/ui (class vocabulary: `bg-card/40`, `border-border/40`, `text-muted-foreground`, `bg-background`, `data-[state=...]`, etc.) |
| Icons | `lucide-react` (DOM shows `lucide lucide-<name>` classes; 17 distinct icons detected: `activity`, `bell`, `brain-circuit`, `chart-candlestick`, `dice-5`, `file-text`, `globe`, `layers`, `layout-dashboard`, `layout-grid`, `menu`, `newspaper`, `plus`, `rotate-ccw`, `search`, `settings`, `shield-check`) |
| Toasts | `sonner` (region `aria-label="Notifications (F8)"` with `ol.fixed.top-0.z-[100]` + `aria-live="polite"` companion region with `aria-label="Notifications alt+T"`) |
| Charts | `recharts` (string match in chunk `e0e14ef0062f765c.js`) |
| Utilities | `clsx` (string match in chunk `ab616ad89ade6d18.js`) |
| Animations | `tailwindcss-animate` v4 primitives (`@keyframes enter`, `exit`, `accordion-down/up`, `caret-blink`) + custom `@keyframes ticker-scroll`, `pulse-dot`, `shimmer` defined in `570f975340a621be.css` |
| Custom CSS | `.grid-bg` (32×32 grid background), `.scrollbar-thin` (6px webkit + firefox thin), `.animate-ticker` (40s linear infinite), `.animate-pulse-dot` (1.6s ease-in-out) |
| Theme | Forced `class="dark"` on `<html>` (no light theme toggle) |
| Fonts | Geist (`geist_a71539c9-module`) + Geist Mono (`geist_mono_8d43a2aa-module`) |

**Libraries the brief requires but the current site does NOT use**: Zustand, TanStack Query, Supabase, Framer Motion. These are net-new in the rebuild.

**Network**: zero XHR / fetch / WebSocket calls observed. Page is entirely self-contained.

---

## 2. Reconstructed Folder Structure (current site)

Inferred from RSC flight payload + chunk graph + DOM (no source maps published):

```
athena-x/                                  # Next.js 16 app-router, Turbopack
├─ app/
│  ├─ layout.tsx                # <html class="dark">, Geist fonts, Toaster, AppShell
│  ├─ page.tsx                  # Renders <Terminal/> (single client island)
│  ├─ globals.css               # Tailwind v4 tokens + @keyframes ticker-scroll/pulse-dot/shimmer
│  └─ error.tsx                 # global error boundary (chunk 58c60a5f)
├─ components/
│  ├─ terminal/
│  │  ├─ terminal-shell.tsx     # <aside> + <header> + <main> + <footer> chrome
│  │  ├─ sidebar.tsx            # branding, MODULES nav (10), WATCHLIST nav (6), footer status
│  │  ├─ topbar.tsx             # ticker tape + module title + search + market status + bell/settings
│  │  ├─ ticker-tape.tsx        # animate-ticker, 12 hardcoded symbols
│  │  ├─ module-nav.tsx         # horizontal 10-button nav under page header
│  │  ├─ page-header.tsx        # icon + h1 + "MODULE N / 10" + description + status banner
│  │  └─ command-palette.tsx    # (placeholder — search box, no actual palette observed)
│  ├─ ui/                       # shadcn/ui primitives (button, card, table, dialog, select, slider, etc.)
│  └─ panels/
│     ├─ panel-chrome.tsx       # collapse/expand, move up/down, drag, hide, remove controls
│     └─ panel-grid.tsx         # responsive grid wrapper
├─ modules/                     # one big file per module (monolithic — inferred)
│  ├─ dashboard/
│  │  └─ dashboard-page.tsx     # 7 widgets, panel-chrome, "Add Widget" / "Reset"
│  ├─ live-market/
│  │  └─ live-market-page.tsx   # provider table + 6 panels + TradingView iframe
│  ├─ technical-analysis/
│  │  └─ technical-analysis-page.tsx
│  ├─ news-intelligence/
│  │  └─ news-intelligence-page.tsx
│  ├─ options-intelligence/
│  │  └─ options-intelligence-page.tsx
│  ├─ macro-intelligence/
│  │  └─ macro-intelligence-page.tsx
│  ├─ ai-forecast/
│  │  └─ ai-forecast-page.tsx
│  ├─ probability-engine/
│  │  └─ probability-engine-page.tsx
│  ├─ report-generator/
│  │  └─ report-generator-page.tsx
│  └─ self-validation/
│     └─ self-validation-page.tsx
├─ lib/
│  ├─ utils.ts                  # cn() — clsx + tailwind-merge
│  ├─ mock-data.ts              # all simulated quotes, news, indicators, chains, macro, forecasts
│  └─ constants.ts              # module list, watchlist, ticker symbols
├─ public/
│  └─ logo.svg
├─ next.config.ts               # Turbopack
├─ tailwind.config.ts           # v4 (CSS-first — most config lives in globals.css @theme)
├─ tsconfig.json
├─ package.json
└─ README.md
```

**Inferred because**: the entire app is one RSC tree and the only client chunks detected are the React/Next framework + a tiny error boundary. The 10 modules are rendered inside one client island (no per-module chunks → no dynamic imports → no code-splitting per module).

---

## 3. Architecture Diagram (current site)

```
┌────────────────────────────────────────────────────────────────────┐
│                         Browser (CSR-only)                          │
│                                                                     │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │   app/layout.tsx  (RSC)                                     │  │
│   │   ─ <html class="dark">, Geist + Geist Mono                 │  │
│   │   ─ <Toaster/> (sonner)                                     │  │
│   │   ─ <TerminalShell>                                         │  │
│   └──────────────────────────────┬──────────────────────────────┘  │
│                                  │                                  │
│                                  ▼                                  │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │   <TerminalShell>  (one big client component)               │  │
│   │                                                             │  │
│   │   state: activeModule (useState, 1..10)                     │  │
│   │   state: activeSymbol (useState, "NVDA")                    │  │
│   │   state: watchlist (useState, hardcoded 6 symbols)          │  │
│   │                                                             │  │
│   │   ┌──────────┐  ┌────────────────────────────────────────┐  │  │
│   │   │ Sidebar  │  │ Topbar (ticker + search + status)      │  │  │
│   │   │ - 10 nav │  │ ────────────────────────────────────── │  │  │
│   │   │ - 6 wl   │  │ ModuleNav (10 buttons)                 │  │  │
│   │   │ - status │  │ ────────────────────────────────────── │  │  │
│   │   └────┬─────┘  │ PageHeader + status banner             │  │  │
│   │        │        │ ────────────────────────────────────── │  │  │
│   │        │  click │ {activeModule === 1 && <Dashboard/>}   │  │  │
│   │        ├───────►│ {activeModule === 2 && <LiveMarket/>}  │  │  │
│   │        │        │ {activeModule === 3 && <TechAnalysis/>}│  │  │
│   │        │        │ … 10 conditional renders                │  │  │
│   │        │        │ ────────────────────────────────────── │  │  │
│   │        │        │ Footer (branding, "Synthetic data")    │  │  │
│   │        │        └────────────────────────────────────────┘  │  │
│   └─────────────────────────────────────────────────────────────┘  │
│                                  ▲                                  │
│                                  │                                  │
│   ┌──────────────────────────────┴──────────────────────────────┐  │
│   │   lib/mock-data.ts  (deterministic generator)               │  │
│   │   ─ quotes[symbol] → { last, bid, ask, high, low, vol, … }  │  │
│   │   ─ news[]         → { id, headline, src, time, cat, … }    │  │
│   │   ─ indicators[]   → { name, value, signal, weight, … }     │  │
│   │   ─ optionChain[]  → { strike, iv, vol, oi, delta, … }      │  │
│   │   ─ macro[]        → { indicator, region, latest, … }       │  │
│   │   ─ forecast[]     → { horizon, scenarios, catalysts, … }   │  │
│   │   ─ trades[]       → { entry, exit, side, pnl, r, … }       │  │
│   │   ─ all updated by setInterval(tick, 1000-5000ms)           │  │
│   └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
│   NO backend • NO Supabase • NO API • NO WebSocket                  │
│   NO Zustand • NO TanStack Query • NO event bus • NO agents         │
└────────────────────────────────────────────────────────────────────┘
```

---

## 4. UI Hierarchy (current site)

```
<html class="dark">
└─ <body class="geist… antialiased bg-background text-foreground">
   ├─ <div class="flex min-h-screen …">                       ◄── app shell
   │  ├─ <aside class="hidden lg:flex w-60 …">                ◄── SIDEBAR
   │  │  ├─ branding header (logo dot + "ATHENA-X" + tagline)
   │  │  ├─ <nav>
   │  │  │  ├─ section "MODULES" → 10 buttons (01..10)
   │  │  │  └─ section "WATCHLIST" → 6 buttons (NVDA AAPL MSFT TSLA SPY BTC-USD)
   │  │  └─ footer (status dot "Engine online" + "v3.2.1")
   │  │
   │  └─ <div class="flex-1 flex flex-col min-w-0">
   │     ├─ <header class="sticky top-0 z-40 …">              ◄── TOPBAR
   │     │  ├─ ticker tape row (h-7, 12 buttons, animate-ticker)
   │     │  ├─ main row (h-14)
   │     │  │  ├─ mobile menu (lg:hidden)
   │     │  │  ├─ module title block (icon + h1 + "MODULE N / 10")
   │     │  │  ├─ search box (max-w-xs, hidden on mobile)
   │     │  │  ├─ market status + clock (hidden on mobile)
   │     │  │  ├─ bell button (with red dot)
   │     │  │  └─ settings button (hidden on mobile)
   │     │
   │     ├─ <main class="flex-1 p-3 md:p-4 lg:p-6 grid-bg">
   │     │  ├─ page header (icon + title + module counter + description)
   │     │  ├─ status banner (active symbol + N widgets + version)
   │     │  ├─ <nav> horizontal module nav (10 icon buttons)
   │     │  └─ <div class="animate-in fade-in duration-300">
   │     │     └─ {active module content}
   │     │
   │     └─ <footer class="mt-8 pt-4 border-t …">
   │        └─ "ATHENA-X v3.2.1 · Quantitative Intelligence Terminal · ● Live · Synthetic data — for demonstration only · © 2026"
   │
   ├─ <div role="region" aria-label="Notifications (F8)">    ◄── sonner Toaster
   │  └─ <ol class="fixed top-0 z-[100] flex flex-col-reverse p-4 sm:bottom-0 sm:right-0 sm:top-auto sm:flex-col md:max-w-[420px]">
   │
   └─ <section aria-label="Notifications alt+T" aria-live="polite">  ◄── sonner a11y region
```

### 4.1 Per-module UI hierarchy (condensed)

**01 Dashboard** (widget grid, all panels share `<PanelChrome>`):
- Market Overview (tile strip with add/remove)
- Watchlist (filter + 6 rows)
- Cross-Module Signals (ALL/LONG/SHORT/NEUTRAL tabs + 6 signals)
- Price Chart (1m/5m/15m/1h/1D selector)
- News Pulse (8 headlines)
- Market Health (composite gauge)
- Sector Heatmap (50+ cells across 6 groups: indices, ETFs, yields, FX, commodities, world, MAG7)
- Top actions: "Add Widget", "Reset"

**02 Live Market Data** (most complex module, ~10 panels):
- Provider Adapters table (yahoo/finnhub/polygon/fred/alphavantage/simulated; columns: status, transport, asset classes, priority, messages, latency, action)
- WebSocket Manager (status panel)
- REST Fallback (status panel)
- Cache + Throttle (status panel)
- Reconnection (status panel)
- Quote Board (6 tabs: Index Futures, US Broad ETFs, Sector ETFs, Volatility, US Treasury Yields, Currencies; full table: LAST/CHG/CHG%/BID/ASK/HIGH/LOW/VOL/SPARK)
- Order Book Depth (visual ladder)
- MAG7 Matrix (7 mini cards: AAPL/MSFT/NVDA/GOOGL/AMZN/META/TSLA)
- World Markets (10 indices: Nikkei, Hang Seng, Shanghai, KOSPI, ASX, FTSE, DAX, CAC, Euro Stoxx, IBEX)
- US Treasury Yield Curve (chart)
- Commodities (6: WTI/Brent/Gold/Silver/Nat Gas/Copper)
- Currencies (4: DXY/EUR-USD/USD-JPY/GBP-USD)
- TradingView Advanced Chart (iframe embedded)

**03 Technical Analysis**:
- Symbol header + timeframe (1m/5m/15m/1h/1D) + chart type (Candles/Line)
- Price Action (chart with MA20/MA50/BB toggles)
- Overall Signal (composite gauge)
- Key Levels (support/resistance)
- Indicator Matrix table (10 indicators × 4 columns: VALUE/SIGNAL/WEIGHT/STRENGTH)

**04 News Intelligence**:
- 4 KPI cards (Total Headlines / Avg Sentiment / Avg Impact / High Impact)
- News Feed (search + category filter + sentiment filter; ~30+ items)
- Sentiment Breakdown (chart)
- Entity Mentions (top 10 chips)
- Impact Distribution (chart)

**05 Options Intelligence**:
- Symbol header
- IV Skew (chart)
- Open Interest by Strike (chart)
- Options Chain (Calls/Both/Puts toggle; full chain: Δ/IV/VOL/OI/BID/ASK × STRIKE × BID/ASK/VOL/OI/IV/Δ)
- Unusual Options Activity (panel)
- IV Term Structure (chart)

**06 Macro Intelligence**:
- US Treasury Yield Curve (chart)
- 10Y vs 2Y — 90D History (chart)
- Economic Indicators table (region filter: All/US/EU/CN/JP/UK/Global; columns: INDICATOR/REGION/FREQ/LATEST/PREVIOUS/SURPRISE/TREND)
- FX Rates (chart)
- Commodities (chart)

**07 AI Forecast Engine**:
- Symbol header + horizon (1D/1W/1M/3M/6M) + "Re-run"
- Price Forecast Trajectory (chart)
- Model Ensemble Breakdown (panel)
- Scenario Analysis (Bull/Base/Bear)
- Forecast Catalysts (list)

**08 Probability Engine**:
- Symbol header + 3 sliders (DTE=30, simulations=200, threshold=35)
- Monte Carlo Simulation Paths (chart)
- Probability of Profit (gauge)
- Terminal Price Distribution (chart)
- Strategy Probability Matrix (table)

**09 Report Generator**:
- Report Configuration (title input + audience select: 5 audiences)
- Timeframe selector (7d/30d/90d/180d)
- Sections multi-select (9 sections: Executive Summary, Market Snapshot, Technical Analysis, News & Sentiment, Options Intelligence, Macro Context, AI Forecast, Risk Assessment, Final Recommendation)
- Generate Report (button)
- Report Preview (panel with View / Export)

**10 Self Validation**:
- Strategy selector (6 options: ATHENA-X Ensemble + 5 individual)
- Equity Curve & Drawdown (chart)
- Strategy Comparison (6 buttons with returns/Sharpe/DD/Ret-DD)
- Model Performance Audit table (5 models × 6 columns: ACC/PREC/REC/SHARPE/MAXDD/CALIB ERR)
- Probability Calibration (chart)
- Trade History table (entry/exit/side/prices/PNL%/R-multiple)
- PnL Distribution (chart)
- Monthly Returns Heatmap

---

## 5. Component Tree (logical)

```
<TerminalShell>                              ← client root, owns global UI state
├─ <Sidebar>
│  ├─ <Brand/>
│  ├─ <NavSection title="Modules">           ← 10× <NavButton>
│  ├─ <NavSection title="Watchlist">         ← 6× <WatchlistButton>
│  └─ <SidebarFooter/>                       ← status + version
├─ <Topbar>
│  ├─ <TickerTape symbols={12 fixed}/>       ← animate-ticker
│  ├─ <ModuleTitle/>
│  ├─ <SymbolSearch/>                        ← textbox only, no palette
│  ├─ <MarketStatus/>                        ← clock + "Live"
│  ├─ <BellButton/>                          ← no-op
│  └─ <SettingsButton/>                      ← no-op
├─ <main>
│  ├─ <PageHeader module={n} total={10}/>
│  ├─ <StatusBanner symbol activeWidgets/>
│  ├─ <ModuleNav>                            ← 10× <ModuleTab>
│  └─ <ActiveModule>                         ← switch (1..10)
│     ├─ <DashboardPage/>
│     │  ├─ <WidgetGrid>                     ← reorderable
│     │  │  └─ <PanelChrome>                 ← shared chrome
│     │  │     ├─ <MarketOverviewPanel/>
│     │  │     ├─ <WatchlistPanel/>
│     │  │     ├─ <CrossModuleSignalsPanel/>
│     │  │     ├─ <PriceChartPanel/>
│     │  │     ├─ <NewsPulsePanel/>
│     │  │     ├─ <MarketHealthPanel/>
│     │  │     └─ <SectorHeatmapPanel/>
│     │  └─ <DashboardActions/>              ← Add Widget / Reset
│     ├─ <LiveMarketPage/>
│     │  ├─ <ProviderAdaptersTable/>
│     │  ├─ <WebSocketManagerPanel/>
│     │  ├─ <RestFallbackPanel/>
│     │  ├─ <CacheThrottlePanel/>
│     │  ├─ <ReconnectionPanel/>
│     │  ├─ <QuoteBoard tabs={6}/>
│     │  ├─ <OrderBookDepth/>
│     │  ├─ <Mag7Matrix/>
│     │  ├─ <WorldMarketsPanel/>
│     │  ├─ <YieldCurvePanel/>
│     │  ├─ <CommoditiesPanel/>
│     │  ├─ <CurrenciesPanel/>
│     │  └─ <TradingViewChart iframe/>
│     ├─ <TechnicalAnalysisPage/>
│     ├─ <NewsIntelligencePage/>
│     ├─ <OptionsIntelligencePage/>
│     ├─ <MacroIntelligencePage/>
│     ├─ <AiForecastPage/>
│     ├─ <ProbabilityEnginePage/>
│     ├─ <ReportGeneratorPage/>
│     └─ <SelfValidationPage/>
└─ <Toaster/>                                ← sonner
```

**Shared component** observed: `<PanelChrome>` (the move-up / move-down / drag / hide / remove control cluster) — but it's **only used on Dashboard and Live Market Data**, not consistently across all modules. Other modules render panels as bare cards without the chrome.

---

## 6. State Management (current)

```
┌──────────────────────────────────────────────────────────────┐
│  <TerminalShell>  (only place with multi-widget state)       │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ useState: activeModule   = 1                            │  │
│  │ useState: activeSymbol   = "NVDA"                       │  │
│  │ useState: watchlist      = ["NVDA","AAPL","MSFT",…]     │  │
│  │ useState: tickerSymbols  = [12 hardcoded symbols]       │  │
│  │ useState: dashboardLayout= [7 widget descriptors]       │  │
│  │ useState: liveMarketLayout=[10 panel descriptors]       │  │
│  └────────────────────────────────────────────────────────┘  │
│         ▲                                                     │
│         │  prop-drilled down to module pages                  │
│         ▼                                                     │
│  Each module page also has its OWN useState for:             │
│   - timeframe, chart type, filters, slider values, etc.      │
│                                                              │
│  Mock data: each module calls lib/mock-data.ts on mount and  │
│  sets up its own setInterval to "tick" the data.             │
└──────────────────────────────────────────────────────────────┘
```

**Findings**:
- No global store. No context providers (other than sonner + React 19 defaults).
- Each module owns its own ticker interval → 10 simultaneous timers when you switch tabs over time.
- `activeSymbol` is the only piece of cross-module state, and it's prop-drilled.
- Watchlist sidebar buttons and topbar ticker tape are **independent** — clicking a watchlist item doesn't change the active symbol of any module (verified by interaction test: clicking NVDA in sidebar doesn't update Technical Analysis symbol).
- No persistence: refresh resets everything.

---

## 7. Data Flow (current)

```
lib/mock-data.ts
  │
  │  (pure functions, deterministic per symbol)
  │
  ├─► DashboardPage        ──►  setInterval(1s)   ──►  local state  ──►  re-render
  ├─► LiveMarketPage       ──►  setInterval(1s)   ──►  local state  ──►  re-render
  ├─► TechnicalAnalysisPage──►  setInterval(2s)   ──►  local state  ──►  re-render
  ├─► NewsIntelligencePage ──►  setInterval(5s)   ──►  local state  ──►  re-render
  ├─► OptionsIntelligencePage► setInterval(3s)    ──►  local state  ──►  re-render
  ├─► MacroIntelligencePage──►  setInterval(10s)  ──►  local state  ──►  re-render
  ├─► AiForecastPage       ──►  (no tick — only on "Re-run")  ──►  local state
  ├─► ProbabilityEnginePage──► (no tick — sliders trigger)   ──►  local state
  ├─► ReportGeneratorPage  ──►  (no tick — Generate triggers) ──►  local state
  └─► SelfValidationPage   ──►  (no tick — strategy switch)   ──►  local state

Cross-module data flow: NONE
   - Dashboard's "Cross-Module Signals" panel is hard-coded mock
   - Dashboard's "News Pulse" panel is hard-coded mock (different from News module's feed)
   - Self Validation's "Strategy Comparison" mentions TA/News/Options/Macro/AI strategies
     but no data is actually pulled from those modules
```

---

## 8. API Flow (current)

```
                    (none)

   Client ────────────────────────────────────────►  (no server)
   
   Zero fetch(), zero XMLHttpRequest, zero WebSocket, zero Supabase,
   zero tRPC, zero GraphQL observed in network panel.
   
   The "Provider Adapters" table in Live Market Data is a STATIC UI
   mock — clicking "FORCE" on finnhub/polygon/etc. changes the row
   label but does not actually trigger any network call.
   
   The TradingView Advanced Chart in Live Market Data is the ONLY
   third-party network call: an iframe to s3.tradingview.com.
```

---

## 9. Event Flow (current)

```
   User click ──► onClick handler ──► setActiveModule(n)  ──►  re-render
                                       └─► unmount old module
                                       └─► mount new module
                                       └─► new module spins up its own interval

   User click on watchlist item ──► (visual highlight only, no state change)

   User types in search ──► (no autocomplete, no submit, no-op)

   User presses F8 ──► (sonner has the binding but no toast is ever fired)

   User presses Alt+T ──► (sonner a11y region — no real binding)

   User presses Ctrl+K ──► (no command palette)
```

There is **no event bus**. There are **no event listeners** other than React's synthetic `onClick`. Cross-module coordination is **nonexistent**.

---

## 10. Agent Communication (current)

**There are no agents in the current site.** The brief asks for agents that communicate through a central event bus; this is a **net-new requirement**.

What the current site *implies* (via UI labels) but does not implement:
- "TA-Engine" (mentioned in Cross-Module Signals)
- "News-Intel" (mentioned in Cross-Module Signals)
- "Options-Flow" (mentioned in Cross-Module Signals)
- "Macro-Model" (mentioned in Cross-Module Signals)
- "AI-Forecast" (mentioned in Cross-Module Signals + AI Forecast Engine module)
- "Prob-Engine" (mentioned in Cross-Module Signals + Probability Engine module)
- 4 AI Forecast sub-models: LSTM Price, Transformer-Seq, GBM Classifier, Random Forest, Logistic Baseline (mentioned in Self Validation)

These are **labels on static UI**, not running processes. The rebuild must promote them to **real agents** that emit/subscribe to events on the bus.

---

## 11. Weaknesses (exhaustive)

### 11.1 Architecture

| # | Weakness | Impact |
|---|---|---|
| W1 | Monolithic single-page tab switching (no URL routing per module) | Back button broken; no deep-linking; no SSR per module; bad SEO; bad UX |
| W2 | No real backend — 100% client-side mock | Cannot be deployed as a real product; cannot persist anything; no auth; no multi-user |
| W3 | No state management library — only ad-hoc useState | State scattered across 10 modules; cross-module state impossible; refresh resets all |
| W4 | No data-fetching layer (no TanStack Query, no SWR) | No caching, no deduplication, no retries, no background refresh, no optimistic updates |
| W5 | No event bus — modules are isolated silos | "Cross-Module Signals" is a lie; AI agents can't talk to each other |
| W6 | No AI agents — only static UIs labeled "engine" | Cannot evolve, cannot be replaced, cannot be tested independently |
| W7 | No persistence layer | User customizations (widgets, panels, watchlist, reports) lost on refresh |
| W8 | No auth/identity | Cannot support multi-tenant, cannot personalize, cannot audit |
| W9 | No error boundaries per module | One module's crash takes down the whole terminal |
| W10 | No code-splitting per module | Single client island loads all 10 modules' code on first paint |
| W11 | No tests (unit, integration, e2e) | Cannot refactor safely; regressions undetected |
| W12 | No environment-based config — providers/symbols/watchlist hardcoded | Cannot deploy to staging/prod with different providers; cannot A/B |
| W13 | No CI/CD hooks (lint, typecheck, test) visible | Quality gates absent |
| W14 | No observability (no logs, no metrics, no traces) | Production incidents invisible |

### 11.2 Modularity

| # | Weakness | Impact |
|---|---|---|
| W15 | Each module is one big file with everything inline (UI + state + data + styling) | Cannot replace one piece without touching the whole module |
| W16 | No README per module | Onboarding impossible |
| W17 | No types per module — TypeScript types are inferred, not exported | Cannot consume a module's API from elsewhere |
| W18 | No services per module — data fetching is inline | Cannot swap mock for real without rewriting UI |
| W19 | No hooks per module — state logic is tangled with JSX | Cannot test business logic independently |
| W20 | No tests per module | See W11 |
| W21 | `<PanelChrome>` is shared but only used on 2 modules — inconsistency | Other modules can't be reordered/hidden/removed |
| W22 | No dependency injection — providers hardcoded | Cannot swap yahoo→polygon without code change |

### 11.3 Data & API

| # | Weakness | Impact |
|---|---|---|
| W23 | "Provider Adapters" table is fake — clicking FORCE does nothing | Misleading UI; violates "no placeholder code" rule |
| W24 | No real WebSocket / REST integration despite UI claiming "WebSocket Manager", "REST Fallback", "Reconnection" | Same as W23 |
| W25 | No cache, no throttle, no rate-limit handling — despite UI claiming "Cache + Throttle" | Same as W23 |
| W26 | All numeric data is deterministic mock — same numbers every refresh | Demo value only; no real signal |
| W27 | TradingView iframe is the only real network call — but it's third-party, uncontrolled, and not integrated with the rest of the app | Walled garden; can't drive other panels from TradingView clicks |

### 11.4 State & Events

| # | Weakness | Impact |
|---|---|---|
| W28 | 10 simultaneous `setInterval` timers (one per module mount) | Memory leak; CPU waste; clock drift |
| W29 | `activeSymbol` is prop-drilled, not centralized | Adding a new consumer requires editing the whole prop chain |
| W30 | Watchlist sidebar items are non-interactive (visual only) | UX dead-end |
| W31 | Ticker tape is hardcoded 12 symbols — not driven by watchlist | Two sources of truth for "what symbols the user cares about" |
| W32 | No undo/redo for layout changes | "Reset" is the only escape hatch |
| W33 | No keyboard navigation other than tab | Power-user hostile |

### 11.5 AI / Agents

| # | Weakness | Impact |
|---|---|---|
| W34 | No actual AI — "AI Forecast Engine" is static numbers | Cannot improve, cannot retrain, cannot A/B |
| W35 | No model registry — 5 models listed in Self Validation are labels | Cannot swap a model |
| W36 | No backtest engine — "Trade History" is mock | Cannot validate strategies |
| W37 | No agent communication — Cross-Module Signals is hand-curated | Cannot scale to new agents |
| W38 | No calibration loop — "Probability Calibration" is a static chart | Cannot detect model drift |

### 11.6 UX & Accessibility

| # | Weakness | Impact |
|---|---|---|
| W39 | Forced dark mode — no light theme toggle | Accessibility issue for some users |
| W40 | Bell icon and Settings icon are no-ops | Dead UI |
| W41 | Search box has no autocomplete, no submit, no-op | Dead UI |
| W42 | F8 / Alt+T shortcuts are advertised but do nothing | Dead UI |
| W43 | Mobile: sidebar hidden, replaced by hamburger — but module nav becomes horizontal scroll on small screens | Cramped mobile UX |
| W44 | No focus management for modal/dialog (none exist) | Will become an issue when adding real dialogs |
| W45 | No skeleton states — modules flash empty then populate | Visual jank |
| W46 | No error states — modules assume mock always works | Will break silently when real data is added |
| W47 | No empty states — modules always show full data | Will look broken when filter returns 0 rows |

### 11.7 Code Quality (inferred)

| # | Weakness | Impact |
|---|---|---|
| W48 | Hardcoded values everywhere (symbols, intervals, colors, labels) | Violates "no hardcoded values" rule |
| W49 | Duplicate logic — each module reimplements its own interval + mock data fetching | Violates "no duplicate logic" rule |
| W50 | Dead code — Bell/Settings/Search/F8/Alt+T handlers exist but do nothing | Violates "no dead code" rule |
| W51 | No dependency injection — providers, loggers, clocks all implicit | Violates "use DI where appropriate" rule |
| W52 | No event-driven architecture — pure imperative React | Violates "event-driven architecture" rule |

---

## 12. Improvements (target state for STEP 2)

The rebuild will turn each weakness into an explicit architectural decision.

### 12.1 Architectural improvements

| Weakness | Improvement |
|---|---|
| W1 (no routing) | Next.js app-router with one route per module: `/dashboard`, `/live-market`, `/technical-analysis`, …, `/self-validation`. Layout route owns the shell. |
| W2 (no backend) | Supabase Postgres + Edge Functions + Realtime. Schema: `users`, `watchlists`, `signals`, `reports`, `backtests`, `agent_runs`. |
| W3 (no store) | Zustand stores sliced per concern: `useActiveSymbolStore`, `useWatchlistStore`, `useLayoutStore`, `useNotificationsStore`, `useAgentStore`. Cross-cutting store composition via selectors. |
| W4 (no data layer) | TanStack Query with one query key namespace per module. Cache invalidation via Supabase Realtime channels. Optimistic updates for mutations. |
| W5 (no event bus) | `lib/event-bus/` — typed pub/sub (TypeScript discriminated unions). Every agent emits events; every consumer subscribes. No direct agent-to-agent calls. |
| W6 (no agents) | `modules/<m>/agents/` — each module that implies an agent gets a real worker (Web Worker for CPU-heavy, Edge Function for I/O-heavy). All agents talk only to the bus. |
| W7 (no persistence) | Supabase tables + `useSyncExternalStore` bridge for Zustand. Layout prefs, watchlists, reports, backtests persisted per user. |
| W8 (no auth) | Supabase Auth (email + OAuth). Row-level security on every table. |
| W9 (no error boundaries) | One `ErrorBoundary` per module route. Module crashes degrade gracefully with retry button. |
| W10 (no code-splitting) | `next/dynamic` per module route. Below-the-fold panels lazy-loaded. |
| W11 (no tests) | Vitest (unit) + React Testing Library (component) + Playwright (e2e) per module. |
| W12 (no config) | `lib/config/` — Zod-validated env loader. Per-module config files. |
| W13 (no CI) | GitHub Actions: lint → typecheck → test → build → deploy. Runs on every PR. |
| W14 (no observability) | Structured logger (`lib/logger/`) + Sentry for errors + OpenTelemetry for traces. |

### 12.2 Modularity improvements

Every module becomes a self-contained package with this canonical structure (per the brief):

```
modules/<module-name>/
├─ README.md             # what it does, how to develop, public API
├─ config.ts             # Zod-validated config (intervals, thresholds, env vars)
├─ types.ts              # all TypeScript types this module exports
├─ api.ts                # Supabase / Edge Function calls (or mock adapter)
├─ hooks.ts              # TanStack Query hooks + Zustand selectors
├─ components/           # UI components, scoped to this module
│  ├─ <module>-page.tsx  # the route component
│  └─ …
├─ services/             # business logic (pure functions)
├─ agents/               # event-bus agents (optional)
└─ tests/                # unit + component tests
```

**Public façade**: each module exports a single `index.ts` that re-exports only what other modules are allowed to consume. Internal files are not importable outside the module (enforced by ESLint `no-restricted-imports`).

**Dependency rule** (enforced by `eslint-plugin-import`):
```
ui ← components ← hooks ← services ← api ← types
                  ↓
                event-bus
```
No arrow may point backwards. No cross-module imports except through the public façade + the event bus.

### 12.3 Data & API improvements

| Weakness | Improvement |
|---|---|
| W23–W25 (fake provider UI) | Real `lib/market-data/` provider abstraction. Adapters: `YahooAdapter`, `FinnhubAdapter`, `PolygonAdapter`, `FredAdapter`, `AlphaVantageAdapter`, `SimulatedAdapter`. All implement `MarketDataProvider` interface. Active provider chosen via config; runtime swap supported. |
| W26 (mock numbers) | Real data via adapters; mock adapter retained for dev/test only. |
| W27 (TradingView iframe) | Wrap in `<TradingViewChart>` component that emits `chart:symbol-selected` events on the bus; other panels subscribe. |

### 12.4 State & event improvements

| Weakness | Improvement |
|---|---|
| W28 (10 timers) | One global ticker in `lib/market-data/ticker.ts` (single setInterval). Modules subscribe via TanStack Query `staleTime` + Supabase Realtime. |
| W29 (prop-drilled symbol) | `useActiveSymbolStore` (Zustand). Any component reads `useActiveSymbolStore(s => s.symbol)`. |
| W30 (dead watchlist) | Watchlist items emit `watchlist:symbol-selected` events; `useActiveSymbolStore` subscribes. |
| W31 (hardcoded ticker) | `useTickerTapeStore` derives its 12 symbols from `useWatchlistStore` (top 12 by volume). |
| W32 (no undo) | `useLayoutStore` with `zundo` middleware for temporal undo/redo. |
| W33 (no keyboard) | `lib/keyboard/` — cmdk command palette (Ctrl+K) for module switching, symbol search, and actions. |

### 12.5 Agent improvements

Define a canonical agent interface:

```ts
// lib/event-bus/agent.ts
interface Agent<TConfig = unknown> {
  readonly id: string;
  readonly kind: 'ta' | 'news' | 'options' | 'macro' | 'forecast' | 'probability' | 'validator';
  start(config: TConfig): Promise<void>;
  stop(): Promise<void>;
  onEvent(event: BusEvent): void;        // react to incoming events
  // agents emit events via injected bus.publish()
}
```

Agents run as Web Workers (CPU-bound: TA, Options, Probability, Validator) or Edge Functions (I/O-bound: News, Macro, Forecast). They never call each other directly — only via the bus.

**Bus event taxonomy** (typed discriminated union, partial list — to be finalized in STEP 2):

```
market:quote-updated      market:trade-printed      market:level2-updated
news:headline-received    news:sentiment-scored     news:impact-classified
ta:indicator-computed     ta:signal-emitted         ta:level-identified
options:chain-refreshed   options:unusual-activity  options:iv-updated
macro:indicator-released  macro:yield-curve-updated macro:fx-rate-updated
forecast:trajectory-computed  forecast:scenario-updated  forecast:catalyst-detected
probability:simulation-run    probability:profit-scored   probability:strategy-matrix-updated
validator:backtest-run       validator:calibration-updated validator:strategy-compared
ui:symbol-selected          ui:module-changed           ui:layout-updated
ui:widget-added             ui:widget-removed
report:generated            report:exported
```

### 12.6 UX improvements

| Weakness | Improvement |
|---|---|
| W39 (forced dark) | `next-themes` with `light` / `dark` / `system`. Persisted. |
| W40–W42 (dead UI) | Bell opens a notifications drawer (real toasts history); Settings opens a settings dialog (theme, refresh rate, providers); Search opens cmdk palette. |
| W43 (mobile) | Bottom tab bar on mobile, swipeable panels, drawer sidebar. |
| W44 (focus) | `react-focus-lock` for all dialogs; `react-aria` for menu semantics. |
| W45 (skeletons) | One `<Skeleton>` per panel; TanStack Query `isLoading` drives it. |
| W46 (errors) | One `<ErrorState>` per panel with retry button; TanStack Query `isError` drives it. |
| W47 (empty) | One `<EmptyState>` per panel; TanStack Query `data.length === 0` drives it. |

### 12.7 Code quality improvements

| Weakness | Improvement |
|---|---|
| W48 (hardcoded) | `lib/config/` + per-module `config.ts`; all magic numbers extracted. |
| W49 (duplicate) | `lib/market-data/`, `lib/event-bus/`, `lib/ui/` shared infrastructure; modules import, never reimplement. |
| W50 (dead code) | Either wire up or delete — no in-between. Bell/Settings/Search all become functional. |
| W51 (no DI) | `lib/di/` — lightweight container for adapters, loggers, clocks. Tests inject fakes. |
| W52 (no event-driven) | The bus becomes the only allowed cross-module communication channel. |

---

## 13. What the Rebuild Must Preserve (the brand DNA)

Despite all the weaknesses, the current site has a strong product identity. The rebuild must keep:

1. **The 10-module map** — the same 10 modules with the same names and the same conceptual scope. The user already thinks in these terms.
2. **The "MODULE N / 10" page header pattern** — strong wayfinding.
3. **The terminal aesthetic** — dark-first, OKLCH green/red, mono-font numerics, grid background, animated ticker.
4. **The widget/panel metaphor** — collapsible, reorderable, removable panels (extended to all modules, not just 2).
5. **The "Active symbol: NVDA · N widgets · v1" status banner** — at-a-glance context.
6. **The sidebar structure** — Modules group + Watchlist group + footer status.
7. **The footer signature** — `ATHENA-X v3.x.x · Quantitative Intelligence Terminal · ● Live · © YYYY`.
8. **The 6-section cross-module signal taxonomy** — TA-Engine, News-Intel, Options-Flow, Macro-Model, AI-Forecast, Prob-Engine (these become the 6 real agents).
9. **The MAG7 + 10-world-indices + 6-commodities + 4-FX canonical asset watchlists** — already proven UX.
10. **The 5-model ensemble** in Self Validation — LSTM, Transformer-Seq, GBM, Random Forest, Logistic Baseline (these become real model adapters).

---

## 14. Open Questions for the User (to resolve before STEP 2)

These will be confirmed in the next turn before producing the redesigned architecture:

1. **Auth model**: Supabase Auth (email + OAuth) — confirmed by brief, but is multi-tenant required (multiple organizations)?
2. **Real market data**: Should the rebuild wire real provider adapters (yahoo → finnhub → polygon → fred → alphavantage fallback chain), or keep the simulated adapter as default and make real adapters opt-in via env?
3. **AI agents**: Should the 6 agents (TA / News / Options / Macro / Forecast / Probability) be (a) Web Workers running in the browser, (b) Supabase Edge Functions, or (c) Python workers in a separate backend? The brief implies edge functions.
4. **AI model execution**: LSTM / Transformer / GBM / RF / Logistic — should these be (a) ONNX Runtime Web in browser, (b) Supabase Edge Functions calling an external inference API, or (c) mock-only for v1?
5. **Reports**: Should generated reports be (a) PDF only, (b) PDF + Supabase Storage, or (c) Markdown + PDF?
6. **Backtests**: Should Self Validation run real backtests (Python via Edge Function) or replay pre-computed trade history from Supabase?
7. **Persistence scope**: Per-user only, or per-user + per-workspace (shared watchlists)?
8. **Theming**: Dark-only (match current) or dark + light + system?
9. **Deployment target**: Vercel + Supabase, or self-hosted?

---

## 15. STEP 1 Deliverable Summary

This document (`STEP-1-ANALYSIS.md`) plus the supporting screenshots and accessibility-tree snapshots in this directory constitute the complete STEP 1 output:

```
/home/z/my-project/analysis/
├─ STEP-1-ANALYSIS.md                ← this file
├─ dashboard-01.png                  ← Dashboard screenshot
├─ module-02-live-market-data.png
├─ module-03-technical-analysis.png
├─ module-04-news-intelligence.png
├─ module-05-options-intelligence.png
├─ module-06-macro-intelligence.png
├─ module-07-ai-forecast-engine.png
├─ module-08-probability-engine.png
├─ module-09-report-generator.png
├─ module-10-self-validation.png
├─ snap-01-dashboard.txt             ← full accessibility tree per module
├─ snap-02-live-market.txt
├─ snap-03-tech-analysis.txt
├─ snap-04-news.txt
├─ snap-05-options.txt
├─ snap-06-macro.txt
├─ snap-07-ai-forecast.txt
├─ snap-08-probability.txt
├─ snap-09-report-gen.txt
└─ snap-10-self-validation.txt
```

**STEP 2 (next)**: Redesign the architecture as modular packages — one README + Config + Types + API + Hooks + Components + Services + Tests per module — and produce the canonical folder structure for the entire ATHENA-X rebuild.

**STEP 3 (after approval)**: Generate the entire folder structure (skeleton only, no implementation).

**STEP 4 (after approval)**: Implement one module at a time, with `tsc --noEmit` + `next lint` after every module, zero errors before proceeding.
