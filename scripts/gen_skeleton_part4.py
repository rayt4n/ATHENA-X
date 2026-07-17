#!/usr/bin/env python3
"""
ATHENA-X Monorepo Skeleton Generator — STEP 3.5
================================================
Implements the Institutional Data Layer (STEP 3.5):
  - Adds 8 new providers (Databento, TradingEconomics, Reuters, CNN, WSJ, CNBC, SEC, Polymarket)
  - Restructures agents/ into 10 hierarchical divisions with team leaders
  - Adds 8 new database schemas (Options, News, Macro, Validation, AI Memory, Market Replay + splits)
"""

from pathlib import Path
import shutil
import textwrap

ROOT = Path("/home/z/my-project/athena-x")
ROOT.mkdir(parents=True, exist_ok=True)

FILES_WRITTEN = 0

def w(rel: str, content: str) -> None:
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(textwrap.dedent(content).lstrip("\n"))
    global FILES_WRITTEN
    FILES_WRITTEN += 1

# ============================================================================
# 1. ADD 8 NEW PROVIDERS
# ============================================================================

NEW_PROVIDERS = [
    ("databento", "Databento", "REST", "equity, etf, future, option", "Institutional-grade futures and options data. PIT-validated. Requires API key. Used for backtesting and AI training."),
    ("trading-economics", "Trading Economics", "REST", "macro indicators, economic calendar", "Global macro indicators for 196 countries. Requires API key."),
    ("reuters", "Reuters", "REST", "news", "Reuters news wire service. Requires API key or RSS feeds."),
    ("cnn", "CNN Business", "REST", "news, fear-greed", "CNN Business news + Fear & Greed Index. Free."),
    ("wsj", "Wall Street Journal", "REST", "news", "WSJ news. Requires subscription + API key."),
    ("cnbc", "CNBC", "REST", "news", "CNBC financial news. Free RSS + paid API."),
    ("sec", "SEC EDGAR", "REST", "filings, institutional holdings", "SEC EDGAR filings database. Free. 13F quarterly filings, 10-K, 10-Q, 8-K."),
    ("polymarket", "Polymarket", "REST", "prediction markets", "Decentralized prediction market. Event probabilities. Free public API."),
]

for slug, name, transport, asset_classes, notes in NEW_PROVIDERS:
    base = f"providers/{slug}"
    # Skip if already exists
    if (ROOT / base).exists():
        continue
    w(f"{base}/README.md", f'''
# {name} Provider

{notes}

## Metadata

- **Slug**: `{slug}`
- **Transport**: {transport}
- **Asset classes**: {asset_classes}

## Implementation status

- [x] Adapter scaffold (STEP 3.5)
- [ ] Implementation (STEP 4)
- [ ] Tests (STEP 4)
''')

    w(f"{base}/pyproject.toml", f'''
[project]
name = "athena-x-provider-{slug}"
version = "0.1.0"
description = "{name} market data provider for ATHENA-X"
requires-python = ">=3.11"
dependencies = ["httpx>=0.27.0", "websockets>=13.0", "pydantic>=2.9.0"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/athena_x_provider_{slug.replace('-', '_')}"]
''')

    pkg = f"src/athena_x_provider_{slug.replace('-', '_')}"
    w(f"{base}/{pkg}/__init__.py", f'"""{name} provider."""\n__version__ = "0.1.0"\n')

    class_name = "".join(p.title() for p in slug.split("-")) + "Adapter"
    if class_name[0].isdigit():
        class_name = "_" + class_name

    w(f"{base}/{pkg}/adapter.py", f'''
"""{name} market data provider adapter."""
from __future__ import annotations


class {class_name}:
    """
    {name} provider adapter.

    Layer 1 — Provider Adapters (STEP 3.5).
    ONLY downloads data. NEVER calculates, validates, or standardizes.
    Raw payloads are emitted to the bus and written to raw_landing schema.
    """

    name = "{slug}"
    transport = "{transport}"
    asset_classes = "{asset_classes}".split(", ")

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key
''')

    w(f"{base}/{pkg}/types.py", f'"""{name} provider types."""\nfrom __future__ import annotations\n')
    w(f"{base}/tests/__init__.py", "")
    w(f"{base}/tests/test_adapter.py", f'"""Tests for {name} adapter."""\n')

# Update failover.yaml to mention Databento as institutional source
w("providers/failover.yaml", '''
# Provider failover chain (STEP 3.5)
#
# Live market data failover (unchanged):
chain:
  - yahoo
  - finnhub
  - polygon
  - flashalpha
  - fred
  - alphavantage

# Institutional-grade sources (used for backtesting + AI training, not live failover):
institutional:
  - databento          # PIT-validated futures + options

# News providers (run concurrently — News Validator dedupes + ranks):
news:
  - reuters
  - cnn
  - wsj
  - cnbc

# Macro sources (FRED is primary, Trading Economics supplements):
macro:
  - fred
  - trading-economics

# Alternative data sources:
alternative:
  - sec               # SEC EDGAR filings (13F, 10-K, 10-Q, 8-K)
  - polymarket        # Prediction markets
  - cnn               # Fear & Greed Index (separate from news)

# Simulated is never in the production failover chain.
dev_only:
  - simulated
''')

# ============================================================================
# 2. RESTRUCTURE agents/ INTO 10 HIERARCHICAL DIVISIONS
# ============================================================================

# Remove old agents directory
old_agents = ROOT / "agents"
if old_agents.exists():
    shutil.rmtree(old_agents)
    print(f"  ✓ Removed old agents/ directory")

# Helper to scaffold an agent (reused from part 2 with hierarchical paths)
def scaffold_agent(path: str, slug: str, name: str, description: str,
                   subscribes: list[str], publishes: list[str],
                   plugin_deps: list[str] = None,
                   layer: str = "", division: str = "", team: str = "") -> None:
    base = f"agents/{path}/{slug}"
    # Build package name from full path
    path_parts = path.split("/") + [slug]
    pkg_name = "athena_x_agent_" + "_".join(p.replace('-', '_') for p in path_parts if p)
    # Keep package name reasonable length
    if len(pkg_name) > 90:
        pkg_name = "athena_x_agent_" + path_parts[-1].replace('-', '_')

    # Build valid Python class names (strip hyphens, title-case each part)
    def py_class(parts: list[str]) -> str:
        # Remove hyphens and underscores, title-case each segment, join
        clean_parts = []
        for p in parts:
            for sub in p.replace('-', ' ').replace('_', ' ').split():
                clean_parts.append(sub)
        n = "".join(sub.title() for sub in clean_parts)
        if n and n[0].isdigit():
            n = "_" + n
        return n + "Agent"

    def py_manifest(parts: list[str]) -> str:
        clean_parts = []
        for p in parts:
            for sub in p.replace('-', ' ').replace('_', ' ').split():
                clean_parts.append(sub)
        n = "".join(sub.title() for sub in clean_parts)
        if n and n[0].isdigit():
            n = "_" + n
        return n + "Manifest"

    class_name = py_class([slug])
    manifest_name = py_manifest([slug])
    agent_id = f"{path.replace('/', '.')}.{slug}"

    w(f"{base}/README.md", f'''
# {name}

> Division: **{division or path.split('/')[0]}**
> Team: **{team or (path.split('/')[2] if len(path.split('/')) > 2 else '—')}**
> Layer: **{layer}**

{description}

## Event subscriptions

{chr(10).join(f"- `{s}`" for s in subscribes) if subscribes else "- (source agent — no subscriptions)"}

## Event publications

{chr(10).join(f"- `{p}`" for p in publishes) if publishes else "- (sink agent — no publications)"}

## Implementation status

- [x] Scaffold (STEP 3.5)
- [ ] Implementation (STEP 4)
- [ ] Tests (STEP 4)
''')

    deps_list = ['"athena-x-runtime-event-bus"', '"athena-x-runtime-logger"', '"athena-x-runtime-health-monitor"']
    for pd in (plugin_deps or []):
        deps_list.append(f'"athena-x-plugin-{pd.replace(".", "-")}"')
    deps_str = "\n".join(f"    {d}," for d in deps_list)

    w(f"{base}/pyproject.toml", f'''
[project]
name = "{pkg_name}"
version = "0.1.0"
description = "{name} — {division or 'ATHENA-X'} agent"
requires-python = ">=3.11"
dependencies = [
{deps_str}
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/{pkg_name}"]
''')

    w(f"{base}/src/{pkg_name}/__init__.py", f'"""{name} agent."""\n__version__ = "0.1.0"\n')

    subs_str = "\n".join(f'        "{s}",' for s in subscribes) or "        # source agent"
    pubs_str = "\n".join(f'        "{p}",' for p in publishes) or "        # sink agent"
    plugins_str = "\n".join(f'        "{p}",' for p in (plugin_deps or [])) or "        # no plugin deps"

    w(f"{base}/src/{pkg_name}/manifest.py", f'''
"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class {manifest_name}:
    agent_id: str = "{agent_id}"
    name: str = "{name}"
    division: str = "{division or path.split('/')[0]}"
    team: str = "{team or (path.split('/')[2] if len(path.split('/')) > 2 else 'core')}"
    layer: str = "{layer}"
    description: str = {repr(description[:200])}
    version: str = "0.1.0"
    subscribes_to: tuple = (
{subs_str}
    )
    publishes: tuple = (
{pubs_str}
    )
    plugin_dependencies: tuple = (
{plugins_str}
    )
    capabilities: dict = field(default_factory=lambda: {{
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    }})


MANIFEST = {manifest_name}()
''')

    config_class = class_name[:-5] + "Config" if class_name.endswith("Agent") else class_name + "Config"
    w(f"{base}/src/{pkg_name}/config.py", f'''
"""Configuration for {name}."""
from __future__ import annotations
from pydantic import BaseModel


class {config_class}(BaseModel):
    """Instance configuration."""
    enabled: bool = True
''')

    w(f"{base}/src/{pkg_name}/types.py", f'"""Types for {name}."""\nfrom __future__ import annotations\n')

    w(f"{base}/src/{pkg_name}/agent.py", f'''
"""{name} — agent implementation."""
from __future__ import annotations


class {class_name}:
    """
    {name}.

    Division: {division or path.split('/')[0]}
    Layer: {layer}

    Implementation comes in STEP 4 per the order in
    docs/architecture/implementation-order.md.
    """

    agent_id = "{agent_id}"
    division = "{division or path.split('/')[0]}"
    layer = "{layer}"

    def __init__(self, config):
        self.config = config
''')

    w(f"{base}/tests/__init__.py", "")
    w(f"{base}/tests/test_agent.py", f'"""Tests for {name}."""\n')


# === Supervisor (top-level) ===
scaffold_agent("supervisor", "supervisor-agent", "Supervisor AI",
    "Top-level Supervisor. Every division leader reports here. Detects conflicts, checks stale data, "
    "detects failing agents, triggers retries, performs confidence weighting, delegates reports, "
    "runs self-learning, tracks performance statistics.",
    subscribes=["*"], publishes=["supervisor:conflict-detected", "supervisor:agent-failing",
                                  "supervisor:retry-requested", "supervisor:confidence-adjusted"],
    layer="supervisor", division="supervisor", team="core")

# === Division + Team definitions ===
DIVISIONS = [
    {
        "slug": "data-collection",
        "name": "Data Collection Division",
        "layer": "1-provider-adapters",
        "teams": [
            ("market-data", "Market Data Team", [
                ("yahoo-collector", "Yahoo Collector", "Downloads equity/ETF/index data from Yahoo Finance."),
                ("finnhub-collector", "Finnhub Collector", "Downloads real-time equity/ETF data via WebSocket from Finnhub."),
                ("polygon-collector", "Polygon Collector", "Downloads real-time + historical data from Polygon.io."),
                ("databento-collector", "Databento Collector", "Downloads institutional-grade futures/options from Databento (PIT-validated)."),
                ("flashalpha-collector", "FlashAlpha Collector", "Downloads options-focused data from FlashAlpha."),
                ("alphavantage-collector", "Alpha Vantage Collector", "Downloads equity/ETF/currency data from Alpha Vantage."),
            ]),
            ("options-data", "Options Data Team", [
                ("polygon-options-collector", "Polygon Options Collector", "Downloads options chains from Polygon."),
                ("databento-options-collector", "Databento Options Collector", "Downloads institutional options data from Databento."),
                ("flashalpha-options-collector", "FlashAlpha Options Collector", "Downloads options data from FlashAlpha."),
            ]),
            ("news-data", "News Data Team", [
                ("reuters-collector", "Reuters Collector", "Ingests Reuters news wire service."),
                ("cnn-collector", "CNN Collector", "Ingests CNN Business news + Fear & Greed Index."),
                ("wsj-collector", "WSJ Collector", "Ingests Wall Street Journal news."),
                ("cnbc-collector", "CNBC Collector", "Ingests CNBC financial news."),
            ]),
            ("macro-data", "Macro Data Team", [
                ("fred-collector", "FRED Collector", "Downloads US Treasury yields + economic indicators from FRED."),
                ("trading-economics-collector", "Trading Economics Collector", "Downloads global macro indicators from Trading Economics."),
            ]),
            ("alternative-data", "Alternative Data Team", [
                ("sec-collector", "SEC Collector", "Downloads SEC EDGAR filings (13F, 10-K, 10-Q, 8-K)."),
                ("polymarket-collector", "Polymarket Collector", "Downloads prediction market probabilities from Polymarket."),
            ]),
            ("cross-market-data", "Cross-Market Data Team", [
                # 20 cross-market collectors (one per instrument)
            ]),
        ],
    },
    {
        "slug": "validation",
        "name": "Validation Division",
        "layer": "2-validation",
        "teams": [
            ("price-validator", "Price Validator Team", [
                ("price-validator-agent", "Price Validator Agent",
                 "Cross-source price validation. If Yahoo says 752.44, Polygon 752.46, Finnhub 752.45 → tolerance < 0.02 → Verified. If one says 742 → REJECT."),
            ]),
            ("volume-validator", "Volume Validator Team", [
                ("volume-validator-agent", "Volume Validator Agent", "Volume sanity checks. Detects impossible spikes or zero-volume anomalies."),
            ]),
            ("options-validator", "Options Validator Team", [
                ("options-validator-agent", "Options Validator Agent", "IV/Greeks/OI consistency checks. Put-call parity verification."),
            ]),
            ("news-validator", "News Validator Team", [
                ("news-validator-agent", "News Validator Agent", "Duplicate detection + source reputation ranking. Filters manipulation."),
            ]),
            ("time-validator", "Time Validator Team", [
                ("time-validator-agent", "Time Validator Agent", "Timestamp normalization + staleness detection. Rejects out-of-order events."),
            ]),
        ],
    },
    {
        "slug": "standardization",
        "name": "Standardization Division",
        "layer": "3-standardization",
        "teams": [
            ("market-standardization", "Market Standardization Team", [
                ("market-standardizer", "Market Standardizer Agent",
                 "Converts provider market data to canonical schema. close/Close/last/price → last_price. UTC timestamps. Normalized symbols, decimals, units. ONLY writer to market_db."),
            ]),
            ("options-standardization", "Options Standardization Team", [
                ("options-standardizer", "Options Standardizer Agent",
                 "Converts provider options data to canonical schema. ONLY writer to options_db."),
            ]),
            ("news-standardization", "News Standardization Team", [
                ("news-standardizer", "News Standardizer Agent",
                 "Converts provider news to canonical schema. ONLY writer to news_db."),
            ]),
            ("macro-standardization", "Macro Standardization Team", [
                ("macro-standardizer", "Macro Standardizer Agent",
                 "Converts provider macro data to canonical schema. ONLY writer to macro_db."),
            ]),
        ],
    },
    {
        "slug": "technical-analysis",
        "name": "Technical Analysis Division",
        "layer": "5-intelligence",
        "teams": [
            ("trend", "Trend Team", [
                ("trend-agent", "Trend AI", "Detects trend direction and strength using ADX + price action."),
                ("adx-agent", "ADX AI", "Computes ADX and detects trend strength."),
                ("support-resistance-agent", "Support/Resistance AI", "Identifies key support and resistance levels."),
            ]),
            ("indicator", "Indicator Team", [
                ("ema-agent", "EMA AI", "Exponential Moving Average + crossover detection."),
                ("sma-agent", "SMA AI", "Simple Moving Average + crossover detection."),
                ("vwap-agent", "VWAP AI", "Volume-Weighted Average Price + deviation detection."),
                ("rsi-agent", "RSI AI", "Relative Strength Index + overbought/oversold detection."),
                ("macd-agent", "MACD AI", "MACD + bullish/bearish crossover detection."),
                ("atr-agent", "ATR AI", "Average True Range for volatility measurement."),
                ("bollinger-agent", "Bollinger AI", "Bollinger Bands + squeeze/expansion detection."),
                ("stochastic-agent", "Stochastic AI", "Stochastic Oscillator."),
                ("cci-agent", "CCI AI", "Commodity Channel Index."),
                ("williams-r-agent", "Williams %R AI", "Williams %R indicator."),
                ("ichimoku-agent", "Ichimoku AI", "Ichimoku Cloud."),
                ("obv-agent", "OBV AI", "On-Balance Volume."),
                ("multi-timeframe-agent", "Multi-Timeframe AI", "Analyzes trend alignment across 9 timeframes (Monthly→1M)."),
            ]),
            ("pattern", "Pattern Team", [
                ("candlestick-agent", "Candlestick AI", "Recognizes candlestick patterns (doji, hammer, engulfing, etc.)."),
                ("fibonacci-agent", "Fibonacci AI", "Identifies Fibonacci retracement levels."),
                ("elliott-wave-agent", "Elliott Wave AI", "Analyzes Elliott Wave patterns."),
                ("escape-top-agent", "Escape Top AI", "Detects breakout-from-consolidation patterns."),
                ("entry-agent", "Entry AI", "Identifies high-probability entry points."),
                ("pull-up-pattern-agent", "Pull-Up Pattern AI", "Detects pull-up continuation patterns."),
            ]),
            ("wyckoff", "Wyckoff Team", [
                ("wyckoff-agent", "Wyckoff AI", "Detects Wyckoff accumulation/distribution phases."),
            ]),
            ("chan-theory", "Chan Theory Team", [
                ("chan-theory-agent", "Chan Theory AI", "缠论分析 (Bi/Duan/Zhongshu detection)."),
            ]),
            ("volume-price", "Volume/Price Team", [
                ("volume-profile-agent", "Volume Profile AI", "Computes POC/VAH/VAL and volume distribution."),
                ("volume-price-agent", "Volume Price AI", "Analyzes volume-price relationships."),
                ("liquidity-agent", "Liquidity AI", "Detects liquidity pools and liquidity voids."),
                ("smart-money-agent", "Smart Money AI", "Detects order blocks, FVGs, and smart money footprints."),
            ]),
        ],
    },
    {
        "slug": "options-intelligence",
        "name": "Options Intelligence Division",
        "layer": "5-intelligence",
        "teams": [
            ("gamma", "Gamma Team", [
                ("gamma-exposure-agent", "Gamma Exposure AI", "Computes GEX (gamma exposure)."),
                ("gamma-flip-agent", "Gamma Flip AI", "Detects gamma flip transitions."),
            ]),
            ("dealer-positioning", "Dealer Positioning Team", [
                ("dealer-position-agent", "Dealer Position AI", "Estimates dealer positioning."),
            ]),
            ("iv", "IV Team", [
                ("iv-agent", "IV AI", "Computes implied volatility via Brent's method."),
                ("volatility-surface-agent", "Volatility Surface AI", "Builds 3D IV surface across strikes/expiries."),
            ]),
            ("iv-crush", "IV Crush Team", [
                ("iv-crush-agent", "IV Crush AI", "Detects IV crush events post-earnings."),
                ("iv-rank-agent", "IV Rank AI", "Computes IV rank and IV percentile."),
            ]),
            ("flow", "Flow Team", [
                ("option-flow-agent", "Option Flow AI", "Detects unusual options activity."),
            ]),
            ("0dte", "0DTE Team", [
                ("_0dte-agent", "0DTE AI", "Specialized analysis for 0-days-to-expiry options."),
            ]),
            ("max-pain", "Max Pain Team", [
                ("max-pain-agent", "Max Pain AI", "Computes max pain for each expiry."),
                ("open-interest-agent", "Open Interest AI", "Analyzes OI changes and concentrations."),
            ]),
            ("greeks", "Greeks Team", [
                ("greeks-agent", "Greeks AI", "Computes option Greeks (delta, gamma, theta, vega, rho)."),
            ]),
            ("probability-of-profit", "Probability of Profit Team", [
                ("probability-of-profit-agent", "Probability of Profit AI", "Computes PoP for option strategies."),
            ]),
        ],
    },
    {
        "slug": "macro-intelligence",
        "name": "Macro Intelligence Division",
        "layer": "5-intelligence",
        "teams": [
            ("fed", "Fed Team", [
                ("fed-agent", "Fed AI", "Federal Reserve: funds rate, FOMC decisions, balance sheet."),
            ]),
            ("treasury", "Treasury Team", [
                ("treasury-agent", "Treasury AI", "US Treasury yields + yield curve analysis."),
            ]),
            ("economic-calendar", "Economic Calendar Team", [
                ("economic-calendar-agent", "Economic Calendar AI", "CPI, PCE, NFP, GDP, Unemployment releases + surprises."),
            ]),
            ("bond-market", "Bond Market Team", [
                ("bond-market-agent", "Bond Market AI", "Corporate bonds, MBS, credit spreads."),
            ]),
            ("fx", "FX Team", [
                ("fx-agent", "FX AI", "DXY, EUR/USD, USD/JPY, GBP/USD analysis."),
            ]),
            ("oil", "Oil Team", [
                ("oil-agent", "Oil AI", "WTI, Brent crude oil analysis."),
            ]),
            ("gold", "Gold Team", [
                ("gold-agent", "Gold AI", "Gold, Silver, precious metals analysis."),
            ]),
            ("geopolitics", "Geopolitics Team", [
                ("geopolitics-agent", "Geopolitics AI", "Geopolitical events + market impact assessment."),
            ]),
        ],
    },
    {
        "slug": "forecast",
        "name": "Forecast Division",
        "layer": "5-intelligence",
        "teams": [
            ("arima", "ARIMA Team", [
                ("arima-agent", "ARIMA Forecast AI", "Statistical ARIMA model. Lightweight, runs on CPU."),
            ]),
            ("lstm", "LSTM Team", [
                ("lstm-agent", "LSTM Forecast AI", "PyTorch LSTM. NEVER runs in browser — always Python GPU."),
            ]),
            ("transformer", "Transformer Team", [
                ("transformer-agent", "Transformer Forecast AI", "PyTorch Transformer (attention-based). NEVER runs in browser — always Python GPU."),
            ]),
            ("xgboost", "XGBoost Team", [
                ("xgboost-agent", "XGBoost Forecast AI", "XGBoost + CatBoost + LightGBM-large. Python GPU."),
            ]),
            ("tabpfn", "TabPFN Team", [
                ("tabpfn-agent", "TabPFN Forecast AI", "In-context tabular learning. Python GPU."),
            ]),
            ("ensemble", "Ensemble Team", [
                ("ensemble-agent", "Ensemble Forecast AI", "Combines all model outputs using dynamic weights from Self-Correction Division."),
            ]),
        ],
    },
    {
        "slug": "decision-intelligence",
        "name": "Decision Intelligence Division",
        "layer": "6-decision",
        "teams": [
            ("market-regime", "Market Regime Team", [
                ("market-regime-agent", "Market Regime AI",
                 "Classifies regime: trending/ranging/breakout/mean-reversion/high-vol/low-vol/news-driven/option-driven/dealer-controlled."),
            ]),
            ("probability", "Probability Team", [
                ("probability-engine-agent", "Probability Engine AI", "Monte Carlo simulation engine. Configurable DTE, simulations count, threshold."),
                ("probability-tree-agent", "Probability Tree AI", "Builds probability tree of future states."),
            ]),
            ("trade-timing", "Trade Timing Team", [
                ("timeframe-sync-agent", "Timeframe Sync AI",
                 "Multi-timeframe alignment: Monthly → Weekly → Daily → 4H → 1H → 30M → 15M → 5M → 1M → Alignment Score."),
            ]),
            ("scenario-analysis", "Scenario Analysis Team", [
                ("scenario-analysis-agent", "Scenario Analysis AI", "Bull/Base/Bear scenario probabilities."),
                ("ai-consensus-agent", "AI Consensus AI", "Aggregates all decision agents into single consensus view per symbol."),
            ]),
            ("risk-assessment", "Risk Assessment Team", [
                ("expected-move-agent", "Expected Move AI", "Computes expected move from options + historical + ATR."),
                ("volatility-projection-agent", "Volatility Projection AI", "Projects forward volatility using GARCH + ATR + IV term structure."),
            ]),
        ],
    },
    {
        "slug": "self-validation",
        "name": "Self-Validation Division",
        "layer": "5-validation",
        "teams": [
            ("prediction-audit", "Prediction Audit Team", [
                ("prediction-audit-agent", "Prediction Audit Agent", "Audits each forecast against actual outcome. Records errors."),
            ]),
            ("accuracy-tracking", "Accuracy Tracking Team", [
                ("accuracy-tracking-agent", "Accuracy Tracking Agent", "Tracks rolling accuracy per model per regime."),
            ]),
            ("model-comparison", "Model Comparison Team", [
                ("model-comparison-agent", "Model Comparison Agent", "A/B compares models. Identifies winners per market context."),
            ]),
            ("self-correction", "Self-Correction Team", [
                ("self-correction-agent", "Self-Correction Agent",
                 "Adjusts model weights based on accuracy tracking. Updates ai_memory_db + model_weights table."),
            ]),
        ],
    },
    {
        "slug": "dashboard-reporting",
        "name": "Dashboard & Reporting Division",
        "layer": "7-reporting",
        "teams": [
            ("live-dashboard", "Live Dashboard Team", [
                ("live-dashboard-agent", "Live Dashboard Agent",
                 "Pushes real-time updates to the frontend via WebSocket. Subscribes to all events the dashboard needs."),
            ]),
            ("weekly-report", "Weekly Report Team", [
                ("weekly-report-agent", "Weekly Report Agent", "Generates comprehensive weekly reports. Long horizon, deep analysis."),
            ]),
            ("daily-report", "Daily Report Team", [
                ("daily-report-agent", "Daily Report Agent", "Generates end-of-day reports. Trading session recap."),
            ]),
            ("intraday-report", "Intraday Report Team", [
                ("intraday-report-agent", "Intraday Report Agent", "Generates intraday snapshots every 15 minutes during market hours."),
            ]),
            ("alert-engine", "Alert Engine Team", [
                ("alert-engine-agent", "Alert Engine Agent",
                 "Fires alerts on configurable conditions: signal conflicts, regime changes, unusual activity, threshold breaches."),
            ]),
        ],
    },
    {
        "slug": "automation",
        "name": "Automation Division (RESERVED)",
        "layer": "future",
        "teams": [
            ("execution", "Execution Team", [
                ("execution-agent", "Execution AI", "Order placement. Reserved — disabled by feature flag."),
            ]),
            ("risk", "Risk Team", [
                ("risk-agent", "Risk AI", "Pre-trade risk checks. Reserved — disabled by feature flag."),
            ]),
            ("position", "Position Team", [
                ("position-agent", "Position AI", "Position management. Reserved — disabled by feature flag."),
            ]),
            ("broker", "Broker Team", [
                ("broker-agent", "Broker API Adapter", "Broker API integration (IBKR, Alpaca). Reserved — disabled by feature flag."),
            ]),
        ],
    },
]

# Generate division leaders + team leaders + agents
for div in DIVISIONS:
    div_slug = div["slug"]
    div_name = div["name"]
    div_layer = div["layer"]

    # Division leader
    scaffold_agent(
        f"{div_slug}",
        "division-leader",
        f"{div_name} Leader",
        f"Division leader for {div_name}. Reports to Supervisor. Coordinates team leaders, "
        f"handles division-level conflicts, reports division health metrics.",
        subscribes=["*"],  # division leader sees everything in its division
        publishes=["supervisor:agent-failing", "supervisor:retry-requested"],
        layer=div_layer, division=div_slug, team="leadership",
    )

    # Teams
    for team_slug, team_name, team_agents in div["teams"]:
        # Team leader
        scaffold_agent(
            f"{div_slug}/{team_slug}",
            "team-leader",
            f"{team_name} Leader",
            f"Team leader for {team_name} in {div_name}. Reports to division leader. "
            f"Coordinates agents in the team, handles team-level conflicts, reports team health.",
            subscribes=["*"],
            publishes=["supervisor:agent-failing", "supervisor:retry-requested"],
            layer=div_layer, division=div_slug, team=team_slug,
        )

        # Agents in the team
        for agent_slug, agent_name, agent_desc in team_agents:
            subscribes = ["market:bar-closed"] if div_layer == "5-intelligence" else []
            publishes = []
            if div_slug == "technical-analysis":
                publishes = ["ta:indicator-computed", "ta:signal-emitted", "ta:level-identified"]
            elif div_slug == "options-intelligence":
                publishes = ["options:iv-updated", "options:greeks-computed", "options:chain-refreshed",
                             "options:gamma-exposure-updated", "options:max-pain-updated", "options:unusual-activity"]
            elif div_slug == "macro-intelligence":
                publishes = ["macro:indicator-released", "macro:yield-curve-updated", "macro:fx-rate-updated", "macro:commodity-updated"]
            elif div_slug == "forecast":
                publishes = ["forecast:trajectory-computed", "forecast:catalyst-detected"]
            elif div_slug == "decision-intelligence":
                publishes = ["decision:regime-classified", "decision:scenario-updated",
                             "decision:expected-move-updated", "decision:volatility-projected",
                             "decision:probability-tree-updated", "decision:ai-consensus-updated",
                             "decision:timeframe-alignment-updated", "probability:simulation-run"]
            elif div_slug == "self-validation":
                publishes = ["learning:prediction-scored", "learning:weight-adjusted"]
            elif div_slug == "dashboard-reporting":
                publishes = ["report:generation-started", "report:generation-completed",
                             "report:exported", "report:stored"]

            plugin_deps = []
            if div_slug == "technical-analysis":
                # Map agents to plugins
                ta_plugin_map = {
                    "ema-agent": ["indicators.ema"],
                    "sma-agent": ["indicators.sma"],
                    "vwap-agent": ["indicators.vwap"],
                    "rsi-agent": ["indicators.rsi"],
                    "macd-agent": ["indicators.macd"],
                    "adx-agent": ["indicators.adx"],
                    "atr-agent": ["indicators.atr"],
                    "bollinger-agent": ["indicators.bollinger"],
                    "stochastic-agent": ["indicators.stochastic"],
                    "cci-agent": ["indicators.cci"],
                    "williams-r-agent": ["indicators.williams-r"],
                    "ichimoku-agent": ["indicators.ichimoku"],
                    "obv-agent": ["indicators.obv"],
                    "fibonacci-agent": ["indicators.fibonacci"],
                    "candlestick-agent": ["patterns.candlestick"],
                    "elliott-wave-agent": ["patterns.elliott-wave"],
                    "wyckoff-agent": ["patterns.wyckoff"],
                    "chan-theory-agent": ["patterns.chan-theory"],
                    "volume-profile-agent": ["patterns.volume-profile"],
                    "smart-money-agent": ["patterns.smart-money"],
                }
                plugin_deps = ta_plugin_map.get(agent_slug, [])
            elif div_slug == "options-intelligence":
                opt_plugin_map = {
                    "greeks-agent": ["options.greeks"],
                    "iv-agent": ["options.iv"],
                    "volatility-surface-agent": ["options.volatility-surface"],
                    "gamma-exposure-agent": ["options.gamma-exposure"],
                    "max-pain-agent": ["options.max-pain"],
                    "skew-agent": ["options.skew"],
                }
                plugin_deps = opt_plugin_map.get(agent_slug, [])

            scaffold_agent(
                f"{div_slug}/{team_slug}",
                agent_slug,
                agent_name,
                agent_desc,
                subscribes=subscribes,
                publishes=publishes,
                plugin_deps=plugin_deps,
                layer=div_layer, division=div_slug, team=team_slug,
            )

# Cross-market data team — add 20 instrument collectors
CROSS_MARKET_SYMBOLS = [
    ("spy", "SPY", "SPDR S&P 500 ETF — primary intelligence target"),
    ("spx", "SPX", "S&P 500 Index"),
    ("es", "ES", "E-mini S&P 500 Futures"),
    ("qqq", "QQQ", "Invesco QQQ Trust (Nasdaq 100)"),
    ("nq", "NQ", "E-mini Nasdaq 100 Futures"),
    ("iwm", "IWM", "iShares Russell 2000 ETF"),
    ("dia", "DIA", "SPDR Dow Jones Industrial Average ETF"),
    ("soxx", "SOXX", "iShares Semiconductor ETF"),
    ("vix", "VIX", "CBOE Volatility Index"),
    ("vvix", "VVIX", "Volatility of Volatility Index"),
    ("move", "MOVE", "ICE BofA MOVE Index (bond volatility)"),
    ("dxy", "DXY", "US Dollar Index"),
    ("tnx", "TNX", "CBOE 10-Year Treasury Yield"),
    ("gold", "Gold", "Gold spot price"),
    ("oil", "Oil", "WTI Crude Oil"),
    ("copper", "Copper", "Copper futures"),
    ("usdjpy", "USDJPY", "USD/JPY exchange rate"),
    ("europe", "Europe", "European equity markets (aggregate)"),
    ("asia", "Asia", "Asian equity markets (aggregate)"),
    ("crypto", "Crypto", "Crypto markets (BTC, ETH aggregate)"),
]

for slug, label, desc in CROSS_MARKET_SYMBOLS:
    scaffold_agent(
        "data-collection/cross-market-data",
        f"{slug}-collector",
        f"{label} Cross-Market Collector",
        f"Downloads {desc} from the best available provider. Feeds Cross-Market Intelligence.",
        subscribes=[],
        publishes=["cross-market:symbol-state-updated"],
        layer="1-provider-adapters", division="data-collection", team="cross-market-data",
    )

# SPY Intelligence Aggregator (sits in Decision Intelligence, aggregates all cross-market)
scaffold_agent(
    "decision-intelligence/scenario-analysis",
    "spy-intelligence-aggregator",
    "SPY Intelligence Aggregator",
    "Subscribes to all 20 cross-market collectors. Aggregates their state into a unified SPY Intelligence view.",
    subscribes=["cross-market:symbol-state-updated"],
    publishes=["cross-market:spy-intelligence-updated"],
    layer="6-decision", division="decision-intelligence", team="scenario-analysis",
)

# Update agents/README.md
w("agents/README.md", '''
# agents/

All AI agents in ATHENA-X. Hierarchical organization under a single Supervisor
with 10 divisions and ~55 teams (STEP 3.5).

## Hierarchy

```
Supervisor AI
│
├── data-collection/                (Layer 1 — Provider Adapters)
│   ├── division-leader/
│   ├── market-data/                (6 collectors: Yahoo, Finnhub, Polygon, Databento, FlashAlpha, AlphaVantage)
│   ├── options-data/               (3 collectors: Polygon, Databento, FlashAlpha)
│   ├── news-data/                 (4 collectors: Reuters, CNN, WSJ, CNBC)
│   ├── macro-data/                (2 collectors: FRED, Trading Economics)
│   ├── alternative-data/          (2 collectors: SEC, Polymarket)
│   └── cross-market-data/         (20 collectors: SPY, SPX, ES, QQQ, NQ, IWM, DIA, SOXX, VIX, VVIX, MOVE, DXY, TNX, Gold, Oil, Copper, USDJPY, Europe, Asia, Crypto)
│
├── validation/                     (Layer 2 — Data Validation)
│   ├── division-leader/
│   ├── price-validator/
│   ├── volume-validator/
│   ├── options-validator/
│   ├── news-validator/
│   └── time-validator/
│
├── standardization/                (Layer 3 — Standardization)
│   ├── division-leader/
│   ├── market-standardization/    (ONLY writer to market_db)
│   ├── options-standardization/   (ONLY writer to options_db)
│   ├── news-standardization/      (ONLY writer to news_db)
│   └── macro-standardization/     (ONLY writer to macro_db)
│
├── technical-analysis/             (Layer 5 — Intelligence)
│   ├── division-leader/
│   ├── trend/                      (Trend, ADX, Support/Resistance)
│   ├── indicator/                  (EMA, SMA, VWAP, RSI, MACD, ATR, Bollinger, Stochastic, CCI, Williams-R, Ichimoku, OBV, Multi-TF)
│   ├── pattern/                    (Candlestick, Fibonacci, Elliott Wave, Escape Top, Entry, Pull-Up)
│   ├── wyckoff/
│   ├── chan-theory/
│   └── volume-price/              (Volume Profile, Volume Price, Liquidity, Smart Money)
│
├── options-intelligence/           (Layer 5 — Intelligence)
│   ├── division-leader/
│   ├── gamma/                      (GEX, Gamma Flip)
│   ├── dealer-positioning/
│   ├── iv/                         (IV, Vol Surface)
│   ├── iv-crush/                  (IV Crush, IV Rank)
│   ├── flow/                      (Option Flow)
│   ├── 0dte/
│   ├── max-pain/                  (Max Pain, Open Interest)
│   ├── greeks/
│   └── probability-of-profit/
│
├── macro-intelligence/             (Layer 5 — Intelligence)
│   ├── division-leader/
│   ├── fed/
│   ├── treasury/
│   ├── economic-calendar/
│   ├── bond-market/
│   ├── fx/
│   ├── oil/
│   ├── gold/
│   └── geopolitics/
│
├── forecast/                       (Layer 5 — Intelligence)
│   ├── division-leader/
│   ├── arima/
│   ├── lstm/                       (Python GPU — NEVER browser)
│   ├── transformer/                (Python GPU — NEVER browser)
│   ├── xgboost/                    (Python GPU)
│   ├── tabpfn/                     (Python GPU)
│   └── ensemble/                  (combines all models using dynamic weights)
│
├── decision-intelligence/          (Layer 6 — Decision)
│   ├── division-leader/
│   ├── market-regime/
│   ├── probability/               (Probability Engine, Probability Tree)
│   ├── trade-timing/              (Timeframe Sync)
│   ├── scenario-analysis/         (Scenario Analysis, AI Consensus, SPY Intelligence Aggregator)
│   └── risk-assessment/           (Expected Move, Volatility Projection)
│
├── self-validation/                (Layer 5 — Validation)
│   ├── division-leader/
│   ├── prediction-audit/
│   ├── accuracy-tracking/
│   ├── model-comparison/
│   └── self-correction/           (adjusts model_weights, updates ai_memory_db)
│
├── dashboard-reporting/            (Layer 7 — Reporting)
│   ├── division-leader/
│   ├── live-dashboard/            (pushes real-time updates to frontend)
│   ├── weekly-report/
│   ├── daily-report/
│   ├── intraday-report/           (15-min snapshots during market hours)
│   └── alert-engine/              (fires alerts on conditions)
│
└── automation/                     (RESERVED — Change 16)
    ├── division-leader/
    ├── execution/
    ├── risk/
    ├── position/
    └── broker/
```

## Layered architecture (STEP 3.5)

| Layer | Division | Rule |
|---|---|---|
| 1 | data-collection | ONLY download data, NEVER calculate |
| 2 | validation | Cross-source validation, confidence scoring |
| 3 | standardization | Convert to canonical schema, write to Layer 4 |
| 4 | (databases) | 10 separate databases — never mix |
| 5 | technical-analysis, options-intelligence, macro-intelligence, forecast | ONLY read database |
| 6 | decision-intelligence | ONLY combine information, NO calculations |
| 7 | dashboard-reporting | ONLY reads decision database |
| 8 | (frontend) | Dashboard only reads report database |

## Agent file structure

```
agents/<division>/<team>/<agent-slug>/
├── README.md
├── pyproject.toml
├── src/<pkg>/
│   ├── __init__.py
│   ├── manifest.py        # agent manifest (id, division, team, layer, subscriptions, publications)
│   ├── config.py          # Zod-validated config schema
│   ├── types.py
│   └── agent.py           # the agent class
└── tests/
```

## Reporting chain

```
Agent → Team Leader → Division Leader → Supervisor
                                        ↓
                                  (conflict detection,
                                   retry, confidence
                                   weighting, learning)
```

Heartbeats flow upward. Decisions flow downward. Events flow on the bus.

## Supervisor responsibilities (Change 3)

- Detect conflicting signals across divisions
- Check stale data (last update > threshold per asset class)
- Detect failing agents (no heartbeat in N seconds)
- Trigger retries (max 3, exponential backoff)
- Confidence weighting (dynamically adjusted based on accuracy from Self-Validation Division)
- Delegate report generation (to Dashboard & Reporting Division)
- Run self-learning (consumes lessons from ai_memory_db)
- Track performance statistics (per-agent throughput, accuracy, latency)
''')

# ============================================================================
# 3. ADD NEW DATABASE SCHEMAS
# ============================================================================

# Remove old database directory and regenerate
old_db = ROOT / "database"
if old_db.exists():
    shutil.rmtree(old_db)
    print(f"  ✓ Removed old database/ directory")

w("database/README.md", '''
# database/

12 Postgres schemas (10 institutional + 2 infrastructure) per STEP 3.5.

## The 10 Institutional Databases (Layer 4)

| # | Schema | Layer | Writer | Purpose |
|---|---|---|---|---|
| 1 | `market_db` | 4 | standardization.market | Validated + standardized market data (quotes, bars, trades) |
| 2 | `options_db` | 4 | standardization.options | Validated + standardized options data (chains, greeks, IV) |
| 3 | `news_db` | 4 | standardization.news | Validated + standardized news (headlines, sentiment, entities) |
| 4 | `macro_db` | 4 | standardization.macro | Validated + standardized macro (indicators, yields, FX, commodities) |
| 5 | `validation_db` | 4 | validation agents | Validation decisions + quality scores |
| 6 | `ai_db` | 4 | intelligence agents (each owns its tables) | TA signals, options signals, news signals, macro signals, cross-market signals, regime classifications |
| 7 | `forecast_db` | 4 | decision agents | Forecast trajectories, scenarios, expected moves, probability trees, AI consensus |
| 8 | `historical_db` | 4 | report-engine + validator-engine | Reports + backtests |
| 9 | `market_replay_db` | 4 | market-replay-recorder | Minute-by-minute cross-domain snapshots (NEW) |
| 10 | `ai_memory_db` | 4 | self-correction agents | Predictions + outcomes + lessons learned (NEW) |

## Infrastructure schemas

| Schema | Purpose |
|---|---|
| `raw_landing` | Layer 1 raw payloads (provider output as-received) |
| `app` | User workspaces, watchlists, module instances |

## Critical rules

1. **Never mix raw and processed data** — raw goes in `raw_landing`, processed goes in domain databases.
2. **Each database has exactly ONE writer** — enforced by RLS.
3. **Every row carries a `confidence` column** (0.0–1.0) — confidence scoring from Layer 2.
4. **Read access is open** to authenticated users (subject to user RLS).
5. **Writer access is locked** to the designated agent per schema.
''')

# Schema 1: raw_landing
w("database/raw-landing/schema.sql", '''
-- ============================================================================
-- raw_landing — Layer 1 raw payloads (provider output as-received)
-- Writer: any Layer 1 provider adapter
-- ============================================================================
CREATE SCHEMA IF NOT EXISTS raw_landing;

CREATE TABLE IF NOT EXISTS raw_landing.provider_payloads (
    id              BIGSERIAL PRIMARY KEY,
    provider        TEXT NOT NULL,
    endpoint        TEXT NOT NULL,
    symbol          TEXT,
    payload         JSONB NOT NULL,
    received_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    ingest_id       UUID NOT NULL
);
CREATE INDEX idx_raw_payloads_provider_time ON raw_landing.provider_payloads (provider, received_at DESC);
CREATE INDEX idx_raw_payloads_symbol_time   ON raw_landing.provider_payloads (symbol, received_at DESC);

CREATE TABLE IF NOT EXISTS raw_landing.provider_calls (
    id              BIGSERIAL PRIMARY KEY,
    provider        TEXT NOT NULL,
    endpoint        TEXT NOT NULL,
    status_code     INTEGER,
    latency_ms      INTEGER,
    error           TEXT,
    called_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_provider_calls_time ON raw_landing.provider_calls (provider, called_at DESC);
''')

# Schema 2: market_db
w("database/market-db/schema.sql", '''
-- ============================================================================
-- market_db — Layer 4 Database 1: Market
-- Writer: standardization.market ONLY
-- Reader: technical-analysis, options-intelligence, macro-intelligence, decision-intelligence
-- ============================================================================
CREATE SCHEMA IF NOT EXISTS market_db;

CREATE TABLE IF NOT EXISTS market_db.quotes (
    symbol          TEXT NOT NULL PRIMARY KEY,
    last_price      NUMERIC NOT NULL,
    bid             NUMERIC,
    ask             NUMERIC,
    high            NUMERIC,
    low             NUMERIC,
    open            NUMERIC,
    prev_close      NUMERIC,
    volume          BIGINT,
    change          NUMERIC,
    change_percent  NUMERIC,
    -- Layer 2 validation metadata
    confidence      NUMERIC NOT NULL DEFAULT 1.0,
    source_count    INTEGER NOT NULL DEFAULT 1,
    validation_status TEXT NOT NULL DEFAULT 'verified',
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS market_db.bars (
    symbol          TEXT NOT NULL,
    timeframe       TEXT NOT NULL,
    timestamp       BIGINT NOT NULL,
    open            NUMERIC NOT NULL,
    high            NUMERIC NOT NULL,
    low             NUMERIC NOT NULL,
    close           NUMERIC NOT NULL,
    volume          BIGINT NOT NULL,
    confidence      NUMERIC NOT NULL DEFAULT 1.0,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (symbol, timeframe, timestamp)
);

CREATE TABLE IF NOT EXISTS market_db.trades (
    id              BIGSERIAL PRIMARY KEY,
    symbol          TEXT NOT NULL,
    price           NUMERIC NOT NULL,
    size            INTEGER NOT NULL,
    side            TEXT,
    timestamp       BIGINT NOT NULL,
    confidence      NUMERIC NOT NULL DEFAULT 1.0,
    received_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_trades_symbol_time ON market_db.trades (symbol, timestamp DESC);

CREATE TABLE IF NOT EXISTS market_db.cross_market_state (
    symbol          TEXT NOT NULL PRIMARY KEY,
    state           JSONB NOT NULL,
    confidence      NUMERIC NOT NULL DEFAULT 1.0,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
''')

# Schema 3: options_db
w("database/options-db/schema.sql", '''
-- ============================================================================
-- options_db — Layer 4 Database 2: Options
-- Writer: standardization.options ONLY
-- ============================================================================
CREATE SCHEMA IF NOT EXISTS options_db;

CREATE TABLE IF NOT EXISTS options_db.chains (
    symbol          TEXT NOT NULL,
    expiry          DATE NOT NULL,
    chain           JSONB NOT NULL,
    confidence      NUMERIC NOT NULL DEFAULT 1.0,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (symbol, expiry)
);

CREATE TABLE IF NOT EXISTS options_db.greeks (
    symbol          TEXT NOT NULL,
    strike          NUMERIC NOT NULL,
    expiry          DATE NOT NULL,
    option_type     TEXT NOT NULL,
    delta           NUMERIC,
    gamma           NUMERIC,
    theta           NUMERIC,
    vega            NUMERIC,
    rho             NUMERIC,
    confidence      NUMERIC NOT NULL DEFAULT 1.0,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (symbol, strike, expiry, option_type)
);

CREATE TABLE IF NOT EXISTS options_db.iv_surface (
    symbol          TEXT NOT NULL,
    strike          NUMERIC NOT NULL,
    expiry          DATE NOT NULL,
    iv              NUMERIC NOT NULL,
    confidence      NUMERIC NOT NULL DEFAULT 1.0,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (symbol, strike, expiry)
);

CREATE TABLE IF NOT EXISTS options_db.open_interest (
    symbol          TEXT NOT NULL,
    strike          NUMERIC NOT NULL,
    expiry          DATE NOT NULL,
    call_oi         BIGINT,
    put_oi          BIGINT,
    call_vol        BIGINT,
    put_vol         BIGINT,
    confidence      NUMERIC NOT NULL DEFAULT 1.0,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (symbol, strike, expiry)
);
''')

# Schema 4: news_db
w("database/news-db/schema.sql", '''
-- ============================================================================
-- news_db — Layer 4 Database 3: News
-- Writer: standardization.news ONLY
-- ============================================================================
CREATE SCHEMA IF NOT EXISTS news_db;

CREATE TABLE IF NOT EXISTS news_db.headlines (
    id              UUID PRIMARY KEY,
    headline        TEXT NOT NULL,
    body            TEXT,
    url             TEXT,
    source          TEXT NOT NULL,
    source_reputation NUMERIC NOT NULL DEFAULT 0.5,
    symbol          TEXT,
    category        TEXT,
    published_at    TIMESTAMPTZ,
    confidence      NUMERIC NOT NULL DEFAULT 1.0,
    received_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_news_symbol_time ON news_db.headlines (symbol, published_at DESC);
CREATE INDEX idx_news_source_time ON news_db.headlines (source, published_at DESC);

CREATE TABLE IF NOT EXISTS news_db.sentiment (
    headline_id     UUID PRIMARY KEY REFERENCES news_db.headlines (id) ON DELETE CASCADE,
    sentiment       TEXT NOT NULL,
    score           NUMERIC NOT NULL,
    impact          INTEGER,
    model           TEXT NOT NULL,
    confidence      NUMERIC NOT NULL DEFAULT 1.0,
    computed_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS news_db.entities (
    id              BIGSERIAL PRIMARY KEY,
    headline_id     UUID REFERENCES news_db.headlines (id) ON DELETE CASCADE,
    entity          TEXT NOT NULL,
    entity_type     TEXT NOT NULL,
    confidence      NUMERIC NOT NULL DEFAULT 1.0,
    extracted_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_news_entities_lookup ON news_db.entities (entity, extracted_at DESC);

CREATE TABLE IF NOT EXISTS news_db.fear_greed (
    id              BIGSERIAL PRIMARY KEY,
    value           INTEGER NOT NULL,
    classification  TEXT NOT NULL,
    source          TEXT NOT NULL DEFAULT 'cnn',
    confidence      NUMERIC NOT NULL DEFAULT 1.0,
    recorded_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
''')

# Schema 5: macro_db
w("database/macro-db/schema.sql", '''
-- ============================================================================
-- macro_db — Layer 4 Database 4: Macro
-- Writer: standardization.macro ONLY
-- ============================================================================
CREATE SCHEMA IF NOT EXISTS macro_db;

CREATE TABLE IF NOT EXISTS macro_db.indicators (
    indicator       TEXT NOT NULL,
    region          TEXT NOT NULL,
    frequency       TEXT NOT NULL,
    value           NUMERIC NOT NULL,
    previous        NUMERIC,
    surprise        NUMERIC,
    unit            TEXT,
    confidence      NUMERIC NOT NULL DEFAULT 1.0,
    released_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (indicator, region, released_at)
);
CREATE INDEX idx_macro_indicators_lookup ON macro_db.indicators (indicator, region, released_at DESC);

CREATE TABLE IF NOT EXISTS macro_db.yield_curve (
    region          TEXT NOT NULL DEFAULT 'US',
    tenor           TEXT NOT NULL,
    yield           NUMERIC NOT NULL,
    confidence      NUMERIC NOT NULL DEFAULT 1.0,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (region, tenor, updated_at)
);

CREATE TABLE IF NOT EXISTS macro_db.fx_rates (
    pair            TEXT NOT NULL PRIMARY KEY,
    rate            NUMERIC NOT NULL,
    change          NUMERIC,
    confidence      NUMERIC NOT NULL DEFAULT 1.0,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS macro_db.commodities (
    commodity       TEXT NOT NULL PRIMARY KEY,
    price           NUMERIC NOT NULL,
    change          NUMERIC,
    unit            TEXT,
    confidence      NUMERIC NOT NULL DEFAULT 1.0,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS macro_db.economic_calendar (
    id              BIGSERIAL PRIMARY KEY,
    event           TEXT NOT NULL,
    region          TEXT NOT NULL,
    scheduled_at    TIMESTAMPTZ NOT NULL,
    actual          NUMERIC,
    forecast        NUMERIC,
    previous        NUMERIC,
    surprise        NUMERIC,
    confidence      NUMERIC NOT NULL DEFAULT 1.0
);
CREATE INDEX idx_economic_calendar_time ON macro_db.economic_calendar (scheduled_at);
''')

# Schema 6: validation_db
w("database/validation-db/schema.sql", '''
-- ============================================================================
-- validation_db — Layer 4 Database 5: Validation
-- Writer: validation agents (each writes its own tables)
-- ============================================================================
CREATE SCHEMA IF NOT EXISTS validation_db;

CREATE TABLE IF NOT EXISTS validation_db.decisions (
    id              BIGSERIAL PRIMARY KEY,
    validator       TEXT NOT NULL,
    symbol          TEXT,
    payload_hash    TEXT NOT NULL,
    status          TEXT NOT NULL,    -- verified|rejected|degraded
    confidence      NUMERIC NOT NULL,
    sources_checked INTEGER NOT NULL,
    sources_agreed  INTEGER NOT NULL,
    outlier_source  TEXT,
    reason          TEXT,
    decided_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_validation_decisions_lookup ON validation_db.decisions (validator, symbol, decided_at DESC);

CREATE TABLE IF NOT EXISTS validation_db.provider_reliability (
    provider        TEXT NOT NULL,
    date            DATE NOT NULL,
    total_calls     INTEGER NOT NULL DEFAULT 0,
    successful_calls INTEGER NOT NULL DEFAULT 0,
    failed_calls    INTEGER NOT NULL DEFAULT 0,
    avg_latency_ms  NUMERIC,
    reliability_score NUMERIC NOT NULL DEFAULT 1.0,
    PRIMARY KEY (provider, date)
);

CREATE TABLE IF NOT EXISTS validation_db.quality_scores (
    id              BIGSERIAL PRIMARY KEY,
    symbol          TEXT NOT NULL,
    domain          TEXT NOT NULL,    -- market|options|news|macro
    quality_score   NUMERIC NOT NULL,
    issues          JSONB,
    checked_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_quality_scores_lookup ON validation_db.quality_scores (symbol, domain, checked_at DESC);
''')

# Schema 7: ai_db
w("database/ai-db/schema.sql", '''
-- ============================================================================
-- ai_db — Layer 4 Database 6: AI Intelligence (Layer 5 outputs)
-- Writer: each intelligence agent owns its own tables
-- ============================================================================
CREATE SCHEMA IF NOT EXISTS ai_db;

CREATE TABLE IF NOT EXISTS ai_db.ta_signals (
    id              BIGSERIAL PRIMARY KEY,
    agent_id        TEXT NOT NULL,
    symbol          TEXT NOT NULL,
    timeframe       TEXT NOT NULL,
    direction       TEXT NOT NULL,
    strength        TEXT NOT NULL,
    weight          NUMERIC NOT NULL,
    confidence      NUMERIC NOT NULL,
    evidence        JSONB,
    emitted_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_ta_signals_lookup ON ai_db.ta_signals (agent_id, symbol, emitted_at DESC);

CREATE TABLE IF NOT EXISTS ai_db.options_signals (
    id              BIGSERIAL PRIMARY KEY,
    agent_id        TEXT NOT NULL,
    symbol          TEXT NOT NULL,
    signal_type     TEXT NOT NULL,
    value           JSONB NOT NULL,
    confidence      NUMERIC NOT NULL,
    emitted_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_options_signals_lookup ON ai_db.options_signals (agent_id, symbol, emitted_at DESC);

CREATE TABLE IF NOT EXISTS ai_db.news_signals (
    id              BIGSERIAL PRIMARY KEY,
    symbol          TEXT NOT NULL,
    sentiment       TEXT NOT NULL,
    impact          INTEGER NOT NULL,
    confidence      NUMERIC NOT NULL,
    emitted_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ai_db.macro_signals (
    id              BIGSERIAL PRIMARY KEY,
    indicator       TEXT NOT NULL,
    region          TEXT NOT NULL,
    value           NUMERIC NOT NULL,
    trend           TEXT,
    confidence      NUMERIC NOT NULL,
    emitted_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ai_db.cross_market_signals (
    symbol          TEXT NOT NULL PRIMARY KEY,
    state           JSONB NOT NULL,
    confidence      NUMERIC NOT NULL,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ai_db.agent_health (
    agent_id        TEXT NOT NULL,
    timestamp       TIMESTAMPTZ NOT NULL DEFAULT now(),
    running         BOOLEAN NOT NULL,
    cpu             NUMERIC,
    memory          NUMERIC,
    api_latency     NUMERIC,
    queue_length    INTEGER,
    error_count     INTEGER,
    restart_count   INTEGER,
    confidence      NUMERIC,
    version         TEXT,
    PRIMARY KEY (agent_id, timestamp)
);

-- Model weight table (managed by self-correction division)
CREATE TABLE IF NOT EXISTS ai_db.model_weights (
    model_id        TEXT PRIMARY KEY,
    weight          NUMERIC NOT NULL,
    accuracy_7d     NUMERIC,
    accuracy_30d    NUMERIC,
    sample_count    INTEGER NOT NULL DEFAULT 0,
    last_adjusted_at TIMESTAMPTZ,
    last_adjustment_reason TEXT
);
''')

# Schema 8: forecast_db
w("database/forecast-db/schema.sql", '''
-- ============================================================================
-- forecast_db — Layer 4 Database 7: Forecasts + Decisions (Layer 6 outputs)
-- Writer: decision-intelligence agents
-- ============================================================================
CREATE SCHEMA IF NOT EXISTS forecast_db;

CREATE TABLE IF NOT EXISTS forecast_db.regimes (
    symbol          TEXT NOT NULL,
    regime          TEXT NOT NULL,
    confidence      NUMERIC NOT NULL,
    evidence        JSONB,
    classified_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (symbol, classified_at)
);
CREATE INDEX idx_regimes_lookup ON forecast_db.regimes (symbol, classified_at DESC);

CREATE TABLE IF NOT EXISTS forecast_db.trajectories (
    id              UUID PRIMARY KEY,
    symbol          TEXT NOT NULL,
    model_id        TEXT NOT NULL,
    runtime         TEXT NOT NULL,
    horizon         TEXT NOT NULL,
    trajectory      JSONB NOT NULL,
    inference_ms    INTEGER NOT NULL,
    model_version   TEXT NOT NULL,
    confidence      NUMERIC NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_trajectories_lookup ON forecast_db.trajectories (symbol, model_id, created_at DESC);

CREATE TABLE IF NOT EXISTS forecast_db.scenarios (
    symbol          TEXT NOT NULL,
    bull            NUMERIC NOT NULL,
    base            NUMERIC NOT NULL,
    bear            NUMERIC NOT NULL,
    confidence      NUMERIC NOT NULL,
    computed_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (symbol, computed_at)
);

CREATE TABLE IF NOT EXISTS forecast_db.expected_moves (
    symbol          TEXT NOT NULL,
    horizon         TEXT NOT NULL,
    expected_move   NUMERIC NOT NULL,
    confidence      NUMERIC NOT NULL,
    computed_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (symbol, horizon, computed_at)
);

CREATE TABLE IF NOT EXISTS forecast_db.probability_trees (
    symbol          TEXT NOT NULL,
    tree            JSONB NOT NULL,
    confidence      NUMERIC NOT NULL,
    computed_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS forecast_db.ai_consensus (
    symbol          TEXT NOT NULL PRIMARY KEY,
    consensus       TEXT NOT NULL,
    agreement       NUMERIC NOT NULL,
    components      JSONB NOT NULL,
    confidence      NUMERIC NOT NULL,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS forecast_db.simulations (
    id              UUID PRIMARY KEY,
    symbol          TEXT NOT NULL,
    config          JSONB NOT NULL,
    stats           JSONB NOT NULL,
    paths           JSONB,
    confidence      NUMERIC NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS forecast_db.timeframe_alignment (
    symbol          TEXT NOT NULL PRIMARY KEY,
    alignment_score NUMERIC NOT NULL,
    breakdown       JSONB NOT NULL,
    confidence      NUMERIC NOT NULL,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
''')

# Schema 9: historical_db (was historical_reports)
w("database/historical-db/schema.sql", '''
-- ============================================================================
-- historical_db — Layer 4 Database 8: Historical Reports + Backtests
-- Writers: report-engine, validator-engine
-- ============================================================================
CREATE SCHEMA IF NOT EXISTS historical_db;

CREATE TABLE IF NOT EXISTS historical_db.reports (
    id              UUID PRIMARY KEY,
    user_id         UUID NOT NULL REFERENCES auth.users (id) ON DELETE CASCADE,
    symbol          TEXT NOT NULL,
    title           TEXT NOT NULL,
    audience        TEXT NOT NULL,
    timeframe       TEXT NOT NULL,
    sections        JSONB NOT NULL,
    markdown        TEXT NOT NULL,
    json_content    JSONB NOT NULL,
    pdf_path        TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'generating',
    validation_score NUMERIC,
    validation_checks JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at    TIMESTAMPTZ
);
CREATE INDEX idx_reports_user_time ON historical_db.reports (user_id, created_at DESC);
CREATE INDEX idx_reports_symbol    ON historical_db.reports (symbol, created_at DESC);

CREATE TABLE IF NOT EXISTS historical_db.backtests (
    id              UUID PRIMARY KEY,
    user_id         UUID NOT NULL REFERENCES auth.users (id) ON DELETE CASCADE,
    strategy_id     TEXT NOT NULL,
    symbol          TEXT NOT NULL,
    config          JSONB NOT NULL,
    equity_curve    JSONB NOT NULL,
    trade_history   JSONB NOT NULL,
    metrics         JSONB NOT NULL,
    calibration     JSONB,
    started_at      TIMESTAMPTZ NOT NULL,
    completed_at    TIMESTAMPTZ,
    status          TEXT NOT NULL DEFAULT 'running'
);
CREATE INDEX idx_backtests_user_time ON historical_db.backtests (user_id, started_at DESC);
''')

# Schema 10: market_replay_db (NEW)
w("database/market-replay-db/schema.sql", '''
-- ============================================================================
-- market_replay_db — Layer 4 Database 9: Market Replay (NEW)
-- Writer: market-replay-recorder agent ONLY
-- Purpose: Store everything, every minute. For backtesting, AI training,
--          debugging decisions, improving forecasts.
-- ============================================================================
CREATE SCHEMA IF NOT EXISTS market_replay_db;

CREATE TABLE IF NOT EXISTS market_replay_db.minute_snapshots (
    snapshot_id      BIGSERIAL PRIMARY KEY,
    timestamp        TIMESTAMPTZ NOT NULL,
    trading_date     DATE NOT NULL,
    session          TEXT NOT NULL,           -- 'pre'|'regular'|'post'
    -- Cross-domain snapshot (each is a JSONB blob)
    market_snapshot  JSONB NOT NULL,          -- quotes for all tracked symbols
    options_snapshot JSONB,                   -- chains + greeks + IV
    news_snapshot    JSONB,                   -- headlines received this minute
    macro_snapshot   JSONB,                   -- macro indicators updated
    gamma_snapshot   JSONB,                   -- GEX + gamma flip per symbol
    darkpool_snapshot JSONB,                  -- dark pool prints
    breadth_snapshot JSONB,                   -- advance/decline, new highs/lows
    confidence       NUMERIC NOT NULL DEFAULT 1.0,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_replay_date_time ON market_replay_db.minute_snapshots (trading_date, timestamp);
CREATE INDEX idx_replay_session    ON market_replay_db.minute_snapshots (trading_date, session);

-- Tick-level replay (for ultra-fine backtesting)
CREATE TABLE IF NOT EXISTS market_replay_db.tick_events (
    id               BIGSERIAL PRIMARY KEY,
    timestamp        TIMESTAMPTZ NOT NULL,
    symbol           TEXT NOT NULL,
    event_type       TEXT NOT NULL,           -- 'trade'|'quote'|'level2'|'news'|'option_print'
    payload          JSONB NOT NULL,
    confidence       NUMERIC NOT NULL DEFAULT 1.0
);
CREATE INDEX idx_replay_ticks_symbol_time ON market_replay_db.tick_events (symbol, timestamp);
CREATE INDEX idx_replay_ticks_time         ON market_replay_db.tick_events (timestamp);
''')

# Schema 11: ai_memory_db (NEW)
w("database/ai-memory-db/schema.sql", '''
-- ============================================================================
-- ai_memory_db — Layer 4 Database 10: AI Memory (NEW)
-- Writer: self-correction division agents ONLY
-- Purpose: Store what the AI concluded, why, and whether it was right.
--          Enables continuous self-improvement.
-- ============================================================================
CREATE SCHEMA IF NOT EXISTS ai_memory_db;

-- Every prediction ever made
CREATE TABLE IF NOT EXISTS ai_memory_db.predictions (
    prediction_id     UUID PRIMARY KEY,
    timestamp         TIMESTAMPTZ NOT NULL,
    agent_id          TEXT NOT NULL,
    model_id          TEXT,
    symbol            TEXT NOT NULL,
    prediction_type   TEXT NOT NULL,           -- 'price'|'direction'|'regime'|'probability'
    prediction_value  JSONB NOT NULL,
    horizon           TEXT NOT NULL,           -- '1D'|'1W'|'1M'
    reason            TEXT,
    evidence          JSONB,
    confidence        NUMERIC NOT NULL,
    -- Outcome (filled in later when the horizon elapses)
    actual_value      JSONB,
    outcome_timestamp TIMESTAMPTZ,
    error             NUMERIC,
    absolute_error    NUMERIC,
    squared_error     NUMERIC,
    -- Learning signal
    lessons_learned   JSONB
);
CREATE INDEX idx_predictions_agent_time ON ai_memory_db.predictions (agent_id, timestamp DESC);
CREATE INDEX idx_predictions_symbol_time ON ai_memory_db.predictions (symbol, timestamp DESC);
CREATE INDEX idx_predictions_unscored   ON ai_memory_db.predictions (timestamp) WHERE actual_value IS NULL;

-- Rolling accuracy per agent per period
CREATE TABLE IF NOT EXISTS ai_memory_db.agent_performance (
    agent_id          TEXT NOT NULL,
    period            TEXT NOT NULL,           -- '7d'|'30d'|'90d'|'all'
    accuracy          NUMERIC,
    precision         NUMERIC,
    recall            NUMERIC,
    sharpe            NUMERIC,
    max_drawdown      NUMERIC,
    sample_count      INTEGER,
    computed_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (agent_id, period, computed_at)
);

-- Lessons the AI has derived (and whether they've been applied)
CREATE TABLE IF NOT EXISTS ai_memory_db.lessons (
    lesson_id         BIGSERIAL PRIMARY KEY,
    timestamp         TIMESTAMPTZ NOT NULL DEFAULT now(),
    lesson_type       TEXT NOT NULL,           -- 'indicator-reliability'|'model-regime-fit'|'fomc-failure'|...
    description       TEXT NOT NULL,
    evidence          JSONB,
    applied           BOOLEAN DEFAULT false,
    applied_at        TIMESTAMPTZ
);

-- Answers to "which indicator/model/combination works best in which context"
CREATE TABLE IF NOT EXISTS ai_memory_db.insights (
    insight_id        BIGSERIAL PRIMARY KEY,
    generated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    question          TEXT NOT NULL,           -- e.g., "which model performs best in trending markets?"
    answer            TEXT NOT NULL,
    supporting_data   JSONB,
    confidence        NUMERIC NOT NULL
);
''')

# Schema 12: app (unchanged)
w("database/app/schema.sql", '''
-- ============================================================================
-- app — User-facing application data
-- Writers: frontend (via Supabase Auth + RLS)
-- ============================================================================
CREATE SCHEMA IF NOT EXISTS app;

CREATE TABLE IF NOT EXISTS app.workspaces (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES auth.users (id) ON DELETE CASCADE,
    name            TEXT NOT NULL,
    main_indicator  TEXT NOT NULL DEFAULT 'SPY' CHECK (main_indicator IN ('ES', 'SPY')),
    panel_layout    JSONB NOT NULL DEFAULT '[]'::jsonb,
    background_services JSONB NOT NULL DEFAULT '[]'::jsonb,
    settings        JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS app.watchlists (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id    UUID NOT NULL REFERENCES app.workspaces (id) ON DELETE CASCADE,
    symbol          TEXT NOT NULL,
    asset_class     TEXT NOT NULL,
    position        INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS app.module_instances (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id    UUID NOT NULL REFERENCES app.workspaces (id) ON DELETE CASCADE,
    module_id       TEXT NOT NULL,
    config          JSONB NOT NULL DEFAULT '{}'::jsonb,
    state           JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Model registry (AI model artifacts)
CREATE TABLE IF NOT EXISTS app.model_artifacts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id        TEXT NOT NULL,
    version         TEXT NOT NULL,
    runtime         TEXT NOT NULL,
    storage_path    TEXT NOT NULL,
    input_schema    JSONB NOT NULL,
    output_schema   JSONB NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (model_id, version)
);
''')

# Updated migration file
w("database/migrations/20260102000000_step_3_5_institutional_databases.sql", '''
-- ============================================================================
-- STEP 3.5 Migration: 12 schemas (10 institutional + 2 infrastructure)
-- Replaces the 4-schema layout from STEP 3.
-- Run order: this file first, then the 11 schema files below in order.
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS raw_landing;
CREATE SCHEMA IF NOT EXISTS market_db;
CREATE SCHEMA IF NOT EXISTS options_db;
CREATE SCHEMA IF NOT EXISTS news_db;
CREATE SCHEMA IF NOT EXISTS macro_db;
CREATE SCHEMA IF NOT EXISTS validation_db;
CREATE SCHEMA IF NOT EXISTS ai_db;
CREATE SCHEMA IF NOT EXISTS forecast_db;
CREATE SCHEMA IF NOT EXISTS historical_db;
CREATE SCHEMA IF NOT EXISTS market_replay_db;
CREATE SCHEMA IF NOT EXISTS ai_memory_db;
CREATE SCHEMA IF NOT EXISTS app;

COMMENT ON SCHEMA raw_landing       IS 'Layer 1 raw provider payloads';
COMMENT ON SCHEMA market_db         IS 'Layer 4 Database 1 — Market (writer: standardization.market)';
COMMENT ON SCHEMA options_db        IS 'Layer 4 Database 2 — Options (writer: standardization.options)';
COMMENT ON SCHEMA news_db           IS 'Layer 4 Database 3 — News (writer: standardization.news)';
COMMENT ON SCHEMA macro_db          IS 'Layer 4 Database 4 — Macro (writer: standardization.macro)';
COMMENT ON SCHEMA validation_db     IS 'Layer 4 Database 5 — Validation (writers: validation agents)';
COMMENT ON SCHEMA ai_db             IS 'Layer 4 Database 6 — AI Intelligence (writers: intelligence agents)';
COMMENT ON SCHEMA forecast_db       IS 'Layer 4 Database 7 — Forecasts + Decisions (writers: decision agents)';
COMMENT ON SCHEMA historical_db     IS 'Layer 4 Database 8 — Historical Reports + Backtests (writers: report-engine, validator-engine)';
COMMENT ON SCHEMA market_replay_db  IS 'Layer 4 Database 9 — Market Replay (writer: market-replay-recorder)';
COMMENT ON SCHEMA ai_memory_db      IS 'Layer 4 Database 10 — AI Memory (writers: self-correction agents)';
COMMENT ON SCHEMA app               IS 'User workspaces, watchlists, module instances';
''')

# Updated RLS policies
w("database/policies/rls.sql", '''
-- ============================================================================
-- Row-Level Security policies (STEP 3.5)
-- ============================================================================

-- User-owned tables (workspaces, watchlists, module_instances, reports, backtests)
ALTER TABLE app.workspaces               ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.watchlists               ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.module_instances         ENABLE ROW LEVEL SECURITY;
ALTER TABLE historical_db.reports        ENABLE ROW LEVEL SECURITY;
ALTER TABLE historical_db.backtests      ENABLE ROW LEVEL SECURITY;

CREATE POLICY "users own workspaces" ON app.workspaces
    USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());
CREATE POLICY "users own watchlists" ON app.watchlists
    USING (EXISTS (SELECT 1 FROM app.workspaces WHERE id = workspace_id AND user_id = auth.uid()));
CREATE POLICY "users own module_instances" ON app.module_instances
    USING (EXISTS (SELECT 1 FROM app.workspaces WHERE id = workspace_id AND user_id = auth.uid()));
CREATE POLICY "users own reports" ON historical_db.reports
    USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());
CREATE POLICY "users own backtests" ON historical_db.backtests
    USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());

-- Read-only access to all Layer 4 databases for authenticated users
-- (write access is locked to service role, which bypasses RLS)
CREATE POLICY "authenticated read market_db"     ON market_db.quotes       FOR SELECT TO authenticated USING (true);
CREATE POLICY "authenticated read options_db"    ON options_db.chains      FOR SELECT TO authenticated USING (true);
CREATE POLICY "authenticated read news_db"       ON news_db.headlines      FOR SELECT TO authenticated USING (true);
CREATE POLICY "authenticated read macro_db"      ON macro_db.indicators    FOR SELECT TO authenticated USING (true);
CREATE POLICY "authenticated read validation_db" ON validation_db.decisions FOR SELECT TO authenticated USING (true);
CREATE POLICY "authenticated read ai_db"         ON ai_db.ta_signals       FOR SELECT TO authenticated USING (true);
CREATE POLICY "authenticated read forecast_db"   ON forecast_db.regimes    FOR SELECT TO authenticated USING (true);
CREATE POLICY "authenticated read replay_db"     ON market_replay_db.minute_snapshots FOR SELECT TO authenticated USING (true);
CREATE POLICY "authenticated read memory_db"     ON ai_memory_db.predictions FOR SELECT TO authenticated USING (true);

-- Service role bypasses RLS (for backend agents).
-- Each agent connects with a service-role key restricted to its designated schema
-- via GRANT statements (below).

-- Per-agent writer grants (restrict service role per agent)
GRANT INSERT, UPDATE ON market_db.quotes         TO service_role;
GRANT INSERT, UPDATE ON options_db.chains        TO service_role;
GRANT INSERT, UPDATE ON news_db.headlines        TO service_role;
GRANT INSERT, UPDATE ON macro_db.indicators      TO service_role;
GRANT INSERT ON validation_db.decisions          TO service_role;
GRANT INSERT ON ai_db.ta_signals                 TO service_role;
GRANT INSERT ON ai_db.options_signals            TO service_role;
GRANT INSERT ON forecast_db.regimes              TO service_role;
GRANT INSERT ON forecast_db.trajectories         TO service_role;
GRANT INSERT ON historical_db.reports            TO service_role;
GRANT INSERT ON historical_db.backtests          TO service_role;
GRANT INSERT ON market_replay_db.minute_snapshots TO service_role;
GRANT INSERT ON ai_memory_db.predictions         TO service_role;
''')

# Updated seeds
w("database/seeds/dev_symbols.sql", '''
-- Dev seed data: default watchlist symbols (STEP 3.5)
INSERT INTO app.workspaces (user_id, name, main_indicator)
VALUES ('00000000-0000-0000-0000-000000000000', 'Default', 'SPY')
ON CONFLICT DO NOTHING;

INSERT INTO app.watchlists (workspace_id, symbol, asset_class, position) VALUES
    ('00000000-0000-0000-0000-000000000000', 'NVDA', 'equity', 1),
    ('00000000-0000-0000-0000-000000000000', 'AAPL', 'equity', 2),
    ('00000000-0000-0000-0000-000000000000', 'MSFT', 'equity', 3),
    ('00000000-0000-0000-0000-000000000000', 'TSLA', 'equity', 4),
    ('00000000-0000-0000-0000-000000000000', 'SPY',  'etf',    5),
    ('00000000-0000-0000-0000-000000000000', 'QQQ',  'etf',    6)
ON CONFLICT DO NOTHING;
''')

# Update top-level README to mention STEP 3.5
w("README.md", '''
# ATHENA-X

> Institutional-grade quantitative intelligence terminal.
> Modular · Plugin-based · Event-driven · AI-supervised · Self-learning.
> Strict 8-layer data pipeline (STEP 3.5).

## What this is

ATHENA-X is a Bloomberg-style market intelligence platform built around
a strict layered architecture (STEP 3.5):

```
Layer 8 ─ Dashboard            ◄── reads Report Database only
            ▲
Layer 7 ─ Report Generator     ◄── reads Decision Database only
            ▲
Layer 6 ─ Decision Agents      ◄── combine information, NO calculations
            ▲
Layer 5 ─ Intelligence Agents  ◄── EMA, RSI, MACD, Chan Theory, Wyckoff, Gamma, etc.
                                  ONLY read database
            ▲
Layer 4 ─ Institutional Database (10 separate databases — never mix)
            ▲
Layer 3 ─ Standardization Agents
            ▲
Layer 2 ─ Data Validation Agents
            ▲
Layer 1 ─ Provider Adapters    ◄── ONLY download data, NEVER calculate
```

**Nothing above Layer 1 calls providers directly.**
**Nothing above Layer 3 touches raw data.**
**The dashboard never calculates — it only displays.**

## Repository layout

| Directory | Purpose |
|---|---|
| `apps/` | Deployable applications (Next.js dashboard, Python backend) |
| `packages/` | Shared, framework-agnostic packages |
| `agents/` | All AI agents — hierarchical under Supervisor (10 divisions × ~55 teams) |
| `engines/` | Orchestration frameworks (data, AI runtime, backtest, etc.) |
| `plugins/` | Installable indicator/pattern/options plugins |
| `providers/` | 14 market data provider adapters |
| `schemas/` | Single source of truth for events, DB, AI models |
| `database/` | 12 schemas (10 institutional + 2 infrastructure) |
| `runtime/` | Bus, queue, scheduler, health, logging, metrics |
| `docs/` | Architecture, ADRs, runbooks |
| `tests/` | Cross-cutting e2e/load tests |
| `scripts/` | Dev/utility scripts |
| `tools/` | Internal scaffolding tooling |
| `configs/` | Environment-specific configs |

## Status

**STEP 3.5** — Institutional Data Layer complete. Skeleton ready.

See `docs/architecture/STEP-3.5-ARCHITECTURE.md` for the authoritative spec.

## Quick start

```bash
# Frontend (Next.js dashboard)
cd apps/nextjs-dashboard && pnpm install && pnpm dev

# Backend (Python FastAPI)
cd apps/python-backend && uv sync && uv run uvicorn main:app --reload

# Or use the workspace scripts
./scripts/setup-dev.sh
```

## License

Proprietary. © 2026 ATHENA-X.
''')

print(f"\n✅ STEP 3.5 complete: {FILES_WRITTEN} files written/updated under {ROOT}")
