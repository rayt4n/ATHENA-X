#!/usr/bin/env python3
"""
ATHENA-X Monorepo Skeleton Generator — STEP 3, Part 2
======================================================
Generates: providers/, plugins/, agents/, engines/
"""

from pathlib import Path
import json
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
# PROVIDERS/  (7 adapters: yahoo, finnhub, polygon, flashalpha, fred, alphavantage, simulated)
# ============================================================================

w("providers/README.md", '''
# providers/

Market data provider adapters. Each provider implements the same
`MarketDataProvider` interface, allowing the failover chain to swap
between them transparently.

## Failover chain (Change 1.2 of original STEP 2)

```
Yahoo → Finnhub → Polygon → FlashAlpha → FRED → AlphaVantage
```

If a provider fails, `engines/data-engine/aggregator.py` automatically
fails over to the next. Failover events are published on the bus.

## Provider list

| Provider | Transport | Asset classes |
|---|---|---|
| `yahoo` | REST | equity, etf, index, currency, commodity, yield, volatility, future |
| `finnhub` | WebSocket | equity, etf, currency |
| `polygon` | WebSocket | equity, etf, currency, commodity |
| `flashalpha` | REST | equity, etf, options |
| `fred` | REST | yield, macro indicators |
| `alphavantage` | REST | equity, etf, currency |
| `simulated` | — | all (DEV ONLY — never in production) |

## Interface contract

```python
class MarketDataProvider(Protocol):
    name: str
    async def fetch_quote(self, symbol: str) -> Quote: ...
    async def fetch_bars(self, symbol: str, timeframe: Timeframe, count: int) -> list[Bar]: ...
    async def fetch_option_chain(self, symbol: str, expiry: date) -> OptionChain: ...
    async def health_check(self) -> ProviderHealth: ...
```
''')

PROVIDERS = [
    ("yahoo",        "Yahoo Finance",       "REST",      "equity, etf, index, currency, commodity, yield, volatility, future", "Free public API. No key required."),
    ("finnhub",      "Finnhub",             "WebSocket", "equity, etf, currency", "Real-time trades. Requires API key."),
    ("polygon",      "Polygon.io",          "WebSocket", "equity, etf, currency, commodity", "Real-time + historical. Requires API key."),
    ("flashalpha",   "FlashAlpha",          "REST",      "equity, etf, options", "Options focus. Requires API key."),
    ("fred",         "FRED (St. Louis Fed)", "REST",     "yield, macro indicators", "Yield curve + economic data. Free API key."),
    ("alphavantage", "Alpha Vantage",       "REST",      "equity, etf, currency", "Requires API key. Rate-limited free tier."),
    ("simulated",    "Simulated",           "—",         "all", "DEV ONLY. Never used in production. Generates deterministic mock data."),
]

for slug, name, transport, asset_classes, notes in PROVIDERS:
    base = f"providers/{slug}"
    w(f"{base}/README.md", f'''
# {name} Provider

{notes}

## Metadata

- **Slug**: `{slug}`
- **Transport**: {transport}
- **Asset classes**: {asset_classes}
- **Failover priority**: see `providers/failover.yaml`

## Implementation status

- [x] Adapter scaffold
- [ ] Quote fetching (STEP 4)
- [ ] Bar fetching (STEP 4)
- [ ] Option chain fetching (STEP 4) [if applicable]
- [ ] Health check (STEP 4)
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

    w(f"{base}/{pkg}/adapter.py", f'''
"""{name} market data provider adapter."""
from __future__ import annotations
from typing import Protocol


class {slug.title().replace('-', '').replace('_', '')}Adapter:
    """
    {name} provider adapter.

    Implements the MarketDataProvider protocol defined in providers/base.py.
    Implementation comes in STEP 4 per the implementation order in
    docs/architecture/implementation-order.md.
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


# Base provider interface
w("providers/base/README.md", '''
# providers/base

The `MarketDataProvider` Protocol that all providers implement.
Not a runnable package — just a shared interface definition.
''')

w("providers/base/types.py", '''
"""Shared types for all providers."""
from __future__ import annotations
from datetime import date, datetime
from typing import Protocol
from pydantic import BaseModel


class Quote(BaseModel):
    symbol: str
    last: float
    bid: float | None = None
    ask: float | None = None
    high: float | None = None
    low: float | None = None
    open: float | None = None
    prev_close: float | None = None
    volume: int | None = None
    change: float | None = None
    change_percent: float | None = None
    timestamp: datetime


class Bar(BaseModel):
    timestamp: int  # unix-millis
    open: float
    high: float
    low: float
    close: float
    volume: int


class OptionRow(BaseModel):
    strike: float
    call_iv: float | None = None
    call_vol: int | None = None
    call_oi: int | None = None
    call_delta: float | None = None
    put_iv: float | None = None
    put_vol: int | None = None
    put_oi: int | None = None
    put_delta: float | None = None


class OptionChain(BaseModel):
    symbol: str
    expiry: date
    rows: list[OptionRow]


class MarketDataProvider(Protocol):
    """Interface that all provider adapters implement."""
    name: str
    transport: str
    asset_classes: list[str]

    async def fetch_quote(self, symbol: str) -> Quote: ...
    async def fetch_bars(self, symbol: str, timeframe: str, count: int) -> list[Bar]: ...
    async def fetch_option_chain(self, symbol: str, expiry: date) -> OptionChain: ...
    async def health_check(self) -> dict: ...
''')

w("providers/failover.yaml", '''
# Provider failover chain (Change 1.2 of original STEP 2)
# Order: top to bottom. On failure, failover to the next.
chain:
  - yahoo
  - finnhub
  - polygon
  - flashalpha
  - fred
  - alphavantage

# Simulated is never in the production failover chain.
# It's only used in development when ENABLE_SIMULATED=true.
dev_only:
  - simulated
''')

# ============================================================================
# PLUGINS/  (indicators + options + patterns)
# ============================================================================

w("plugins/README.md", '''
# plugins/

Installable indicator, options, and pattern recognition plugins (Change 13).

Every indicator is an independent plugin with a standardized manifest.
Plugins are loaded by `engines/plugin-engine/` at startup.

## Layout

```
plugins/
├── indicators/    # TA computation plugins
├── options/       # options computation plugins
├── patterns/      # pattern recognition plugins
└── dark-pool/     # alternative data plugins (future)
```

## Plugin manifest

Every plugin ships a `manifest.py` (or `manifest.ts` for browser plugins):

```python
@dataclass(frozen=True)
class PluginManifest:
    id: str           # e.g., "indicators.ema"
    name: str         # e.g., "EMA"
    version: str      # semver
    type: str         # indicator | options | pattern | dark-pool
    runtime: str      # python | typescript | wasm
    inputs: list[str]      # e.g., ["closes"]
    params: dict           # e.g., {"period": 20}
    outputs: list[str]     # e.g., ["value", "signal"]
    dependencies: list[str]  # other plugin ids
```

## Adding a new plugin

```bash
python tools/plugin-scaffolder/scaffold.py indicators my_indicator
```

This generates boilerplate under `plugins/indicators/my_indicator/`.
''')

# Indicator plugins
INDICATOR_PLUGINS = [
    ("ema", "Exponential Moving Average", ["closes"], {"period": 20}, ["value", "signal"]),
    ("sma", "Simple Moving Average", ["closes"], {"period": 50}, ["value", "signal"]),
    ("vwap", "Volume-Weighted Average Price", ["highs", "lows", "closes", "volumes"], {}, ["value", "signal"]),
    ("rsi", "Relative Strength Index", ["closes"], {"period": 14}, ["value", "signal"]),
    ("macd", "Moving Average Convergence Divergence", ["closes"], {"fast": 12, "slow": 26, "signal": 9}, ["macd", "signal", "histogram"]),
    ("adx", "Average Directional Index", ["highs", "lows", "closes"], {"period": 14}, ["adx", "plus_di", "minus_di"]),
    ("atr", "Average True Range", ["highs", "lows", "closes"], {"period": 14}, ["value"]),
    ("bollinger", "Bollinger Bands", ["closes"], {"period": 20, "std_dev": 2}, ["upper", "middle", "lower", "percent_b"]),
    ("fibonacci", "Fibonacci Retracement", ["highs", "lows"], {"levels": [0.236, 0.382, 0.5, 0.618, 0.786]}, ["levels"]),
    ("stochastic", "Stochastic Oscillator", ["highs", "lows", "closes"], {"k_period": 14, "d_period": 3}, ["k", "d"]),
    ("cci", "Commodity Channel Index", ["highs", "lows", "closes"], {"period": 20}, ["value"]),
    ("williams-r", "Williams %R", ["highs", "lows", "closes"], {"period": 14}, ["value"]),
    ("ichimoku", "Ichimoku Cloud", ["highs", "lows", "closes"], {}, ["tenkan", "kijun", "senkou_a", "senkou_b", "chikou"]),
    ("obv", "On-Balance Volume", ["closes", "volumes"], {}, ["value"]),
]

for slug, name, inputs, params, outputs in INDICATOR_PLUGINS:
    base = f"plugins/indicators/{slug}"
    w(f"{base}/README.md", f'''
# {name} Plugin

| Field | Value |
|---|---|
| ID | `indicators.{slug}` |
| Type | indicator |
| Runtime | python |
| Inputs | {inputs} |
| Params | {params} |
| Outputs | {outputs} |

## Description

Computes {name.lower()} values for a given series.

## Usage

Loaded by `engines/plugin-engine/` and consumed by the corresponding
TA agent under `agents/raw-intelligence/technical-analysis/{slug}/`.

Implementation comes in STEP 4.
''')

    w(f"{base}/pyproject.toml", f'''
[project]
name = "athena-x-plugin-indicators-{slug}"
version = "0.1.0"
description = "{name} indicator plugin for ATHENA-X"
requires-python = ">=3.11"
dependencies = ["numpy>=2.0.0", "pandas>=2.2.0"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/athena_x_plugin_indicators_{slug.replace('-', '_')}"]
''')

    pkg = f"src/athena_x_plugin_indicators_{slug.replace('-', '_')}"
    w(f"{base}/{pkg}/__init__.py", f'"""{name} plugin."""\n__version__ = "0.1.0"\n')

    w(f"{base}/{pkg}/manifest.py", f'''
"""Plugin manifest — declares capabilities to the plugin-engine."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class {slug.title().replace('-', '').replace('_', '')}Manifest:
    id: str = "indicators.{slug}"
    name: str = "{name}"
    version: str = "0.1.0"
    type: str = "indicator"
    runtime: str = "python"
    inputs: tuple = {tuple(inputs)}
    params: dict = field(default_factory=lambda: {params})
    outputs: tuple = {tuple(outputs)}
    dependencies: tuple = ()


MANIFEST = {slug.title().replace('-', '').replace('_', '')}Manifest()
''')

    w(f"{base}/{pkg}/plugin.py", f'''
"""{name} computation plugin."""
from __future__ import annotations


class {slug.title().replace('-', '').replace('_', '')}Plugin:
    """
    {name} plugin. Implementation comes in STEP 4.

    The plugin-engine calls `compute(inputs, params)` and expects
    a dict matching the manifest's `outputs` field.
    """

    def compute(self, inputs: dict, params: dict) -> dict:
        raise NotImplementedError("STEP 4 implementation")
''')

    w(f"{base}/tests/__init__.py", "")
    w(f"{base}/tests/test_plugin.py", f'"""Tests for {name} plugin."""\n')

# Options plugins
OPTIONS_PLUGINS = [
    ("greeks", "Greeks Calculator", ["spot", "strike", "expiry", "iv", "rate"], ["delta", "gamma", "theta", "vega", "rho"]),
    ("iv", "Implied Volatility Solver", ["spot", "strike", "expiry", "option_price", "type"], ["iv"]),
    ("skew", "IV Skew Calculator", ["iv_chain"], ["skew", "risk_reversal", "butterfly"]),
    ("gamma-exposure", "Gamma Exposure (GEX)", ["option_chain", "spot"], ["gex", "gamma_flip"]),
    ("max-pain", "Max Pain Calculator", ["option_chain"], ["max_pain"]),
    ("volatility-surface", "Volatility Surface Builder", ["option_chain"], ["surface"]),
]

for slug, name, inputs, outputs in OPTIONS_PLUGINS:
    base = f"plugins/options/{slug}"
    w(f"{base}/README.md", f'''
# {name} Plugin

| Field | Value |
|---|---|
| ID | `options.{slug}` |
| Type | options |
| Runtime | python |
| Inputs | {inputs} |
| Outputs | {outputs} |

Implementation comes in STEP 4.
''')

    w(f"{base}/pyproject.toml", f'''
[project]
name = "athena-x-plugin-options-{slug}"
version = "0.1.0"
description = "{name} options plugin for ATHENA-X"
requires-python = ">=3.11"
dependencies = ["numpy>=2.0.0", "scipy>=1.14.0"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/athena_x_plugin_options_{slug.replace('-', '_')}"]
''')

    pkg = f"src/athena_x_plugin_options_{slug.replace('-', '_')}"
    w(f"{base}/{pkg}/__init__.py", f'"""{name} plugin."""\n__version__ = "0.1.0"\n')

    w(f"{base}/{pkg}/manifest.py", f'''
"""Plugin manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class {slug.title().replace('-', '').replace('_', '')}Manifest:
    id: str = "options.{slug}"
    name: str = "{name}"
    version: str = "0.1.0"
    type: str = "options"
    runtime: str = "python"
    inputs: tuple = {tuple(inputs)}
    params: dict = field(default_factory=dict)
    outputs: tuple = {tuple(outputs)}
    dependencies: tuple = ()


MANIFEST = {slug.title().replace('-', '').replace('_', '')}Manifest()
''')

    w(f"{base}/{pkg}/plugin.py", f'''
"""{name} computation plugin."""
from __future__ import annotations


class {slug.title().replace('-', '').replace('_', '')}Plugin:
    """Implementation comes in STEP 4."""

    def compute(self, inputs: dict, params: dict) -> dict:
        raise NotImplementedError("STEP 4 implementation")
''')

    w(f"{base}/tests/__init__.py", "")
    w(f"{base}/tests/test_plugin.py", f'"""Tests for {name} plugin."""\n')

# Pattern plugins
PATTERN_PLUGINS = [
    ("candlestick", "Candlestick Pattern Recognition", ["bars"], ["patterns"]),
    ("elliott-wave", "Elliott Wave Analyzer", ["bars"], ["waves", "current_pattern"]),
    ("wyckoff", "Wyckoff Method Analyzer", ["bars", "volume"], ["phase", "events"]),
    ("chan-theory", "Chan Theory (缠论) Analyzer", ["bars"], ["bi", "duan", "zhongshu"]),
    ("volume-profile", "Volume Profile", ["bars"], ["poc", "vah", "val", "profile"]),
    ("smart-money", "Smart Money Concept Detector", ["bars"], ["order_blocks", "fair_value_gaps", "liquidity"]),
]

for slug, name, inputs, outputs in PATTERN_PLUGINS:
    base = f"plugins/patterns/{slug}"
    w(f"{base}/README.md", f'''
# {name} Plugin

| Field | Value |
|---|---|
| ID | `patterns.{slug}` |
| Type | pattern |
| Runtime | python |
| Inputs | {inputs} |
| Outputs | {outputs} |

Implementation comes in STEP 4.
''')

    w(f"{base}/pyproject.toml", f'''
[project]
name = "athena-x-plugin-patterns-{slug}"
version = "0.1.0"
description = "{name} pattern recognition plugin for ATHENA-X"
requires-python = ">=3.11"
dependencies = ["numpy>=2.0.0", "pandas>=2.2.0", "scipy>=1.14.0"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/athena_x_plugin_patterns_{slug.replace('-', '_')}"]
''')

    pkg = f"src/athena_x_plugin_patterns_{slug.replace('-', '_')}"
    w(f"{base}/{pkg}/__init__.py", f'"""{name} plugin."""\n__version__ = "0.1.0"\n')

    w(f"{base}/{pkg}/manifest.py", f'''
"""Plugin manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class {slug.title().replace('-', '').replace('_', '')}Manifest:
    id: str = "patterns.{slug}"
    name: str = "{name}"
    version: str = "0.1.0"
    type: str = "pattern"
    runtime: str = "python"
    inputs: tuple = {tuple(inputs)}
    params: dict = field(default_factory=dict)
    outputs: tuple = {tuple(outputs)}
    dependencies: tuple = ()


MANIFEST = {slug.title().replace('-', '').replace('_', '')}Manifest()
''')

    w(f"{base}/{pkg}/plugin.py", f'''
"""{name} computation plugin."""
from __future__ import annotations


class {slug.title().replace('-', '').replace('_', '')}Plugin:
    """Implementation comes in STEP 4."""

    def compute(self, inputs: dict, params: dict) -> dict:
        raise NotImplementedError("STEP 4 implementation")
''')

    w(f"{base}/tests/__init__.py", "")
    w(f"{base}/tests/test_plugin.py", f'"""Tests for {name} plugin."""\n')

# ============================================================================
# ENGINES/  (7 engines)
# ============================================================================

ENGINES = [
    ("data-engine", "Data Pipeline Orchestrator",
     "Orchestrates the Data Collection AI pipeline (Change 1):\n"
     "collection → validation → standardization → database.\n"
     "Manages provider failover, timestamp normalization, deduplication,\n"
     "quality scoring, cross-provider validation, historical recording.",
     ["athena-x-runtime-event-bus", "athena-x-runtime-logger", "httpx>=0.27.0", "redis>=5.0.0"]),

    ("ai-runtime", "AI Runtime (GPU)",
     "GPU inference server for heavy models (Change 4):\n"
     "PyTorch (LSTM, Transformer), TabPFN, XGBoost, CatBoost, LightGBM-large.\n"
     "Loads models at startup, keeps them warm in GPU memory, batches requests.\n"
     "LSTM and Transformer NEVER run in the browser — this engine owns them.",
     ["torch>=2.4.0", "xgboost>=2.1.0", "catboost>=1.2.0", "lightgbm>=4.5.0", "tabpfn>=0.1.0"]),

    ("onnx-runtime", "ONNX Runtime (Browser)",
     "Serves browser-runnable ONNX models (Change 4):\n"
     "LightGBM-small, Random Forest, Logistic Regression.\n"
     "Maintains model registry, downloads .onnx files from Supabase Storage,\n"
     "caches in IndexedDB, runs inference via onnxruntime-web (WebGPU).",
     ["onnxruntime>=1.20.0"]),

    ("backtest-engine", "Backtest Engine (vectorbt)",
     "Real Python backtesting engine (Change 6 of STEP 2.1 — never mock).\n"
     "Uses vectorbt to run strategies over historical data.\n"
     "Computes metrics: returns, Sharpe, Sortino, MaxDD, Calmar, win rate.\n"
     "Strategies: athena-ensemble, ta-only, news-only, options-only, macro-only, forecast-only.",
     ["vectorbt>=0.26.0", "pandas>=2.2.0", "numpy>=2.0.0"]),

    ("report-engine", "Report Engine (Multi-format)",
     "Generates reports in 4 formats (Change 5 of original STEP 2):\n"
     "Markdown (canonical) → JSON (structured) → PDF (printable) → Storage.\n"
     "Audiences: Investment Committee, PM, Trader, Client, Research.\n"
     "9 sections: Exec Summary, Market Snapshot, TA, News, Options, Macro, AI Forecast, Risk, Final Rec.",
     ["jinja2>=3.1.0", "weasyprint>=62.0", "markdown>=3.7"]),

    ("plugin-engine", "Plugin Loader & Lifecycle",
     "Discovers, loads, and manages plugin lifecycle (Change 13).\n"
     "Validates plugin manifests against schemas/plugins/manifest.schema.json.\n"
     "Maintains a plugin registry. Hot-reloads plugins in development.\n"
     "Used by all agents that need indicator/options/pattern computations.",
     []),

    ("learning-engine", "Self-Correction Engine",
     "Continuously scores predictions vs actuals (Change 12):\n"
     "prediction → market outcome → compare → error → weight adjustment → improve.\n"
     "Maintains model_weights table in ai_intelligence schema.\n"
     "Adjustments are consumed by Supervisor (Change 3) and Forecast Ensemble.",
     ["scipy>=1.14.0", "numpy>=2.0.0"]),
]

for slug, name, desc, deps in ENGINES:
    base = f"engines/{slug}"
    w(f"{base}/README.md", f'''
# {name}

{desc}

## Implementation status

- [x] Scaffold
- [ ] Implementation (STEP 4)
- [ ] Tests (STEP 4)
''')

    deps_str = "\n".join(f'    "{d}",' for d in deps)
    w(f"{base}/pyproject.toml", f'''
[project]
name = "athena-x-engine-{slug}"
version = "0.1.0"
description = "{name} for ATHENA-X"
requires-python = ">=3.11"
dependencies = [
{deps_str}
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/athena_x_engine_{slug.replace('-', '_')}"]
''')

    pkg = f"src/athena_x_engine_{slug.replace('-', '_')}"
    w(f"{base}/{pkg}/__init__.py", f'"""{name}."""\n__version__ = "0.1.0"\n')

    w(f"{base}/{pkg}/engine.py", f'''
"""{name} core module."""
from __future__ import annotations


class {slug.title().replace('-', '').replace('_', '')}Engine:
    """
    {name}. Implementation comes in STEP 4.

    See docs/architecture/implementation-order.md for the build sequence.
    """
''')

    w(f"{base}/tests/__init__.py", "")
    w(f"{base}/tests/test_engine.py", f'"""Tests for {name}."""\n')

# ============================================================================
# AGENTS/
# ============================================================================

w("agents/README.md", '''
# agents/

All AI agents in ATHENA-X. Each agent is an independent, supervised process
that subscribes to bus events and publishes bus events.

## Layered architecture (Changes 1, 2, 3, 4, 12)

```
agents/
├── data-collection/          (Layer 0: Data Collection AI — Change 1)
│   ├── collection-agent/
│   ├── validation-agent/
│   └── standardization-agent/
│
├── raw-intelligence/         (Layer 1: Raw Intelligence — facts only — Change 2)
│   ├── technical-analysis/   (23 TA agents — Change 6)
│   ├── options/              (15 options agents — Change 7)
│   ├── news/
│   ├── macro/
│   └── cross-market/         (20 cross-market agents — Change 8)
│
├── decision-intelligence/    (Layer 2: Decision Intelligence — conclusions only — Change 2)
│   ├── market-regime/        (Change 9)
│   ├── timeframe-sync/       (Change 10)
│   ├── forecast/             (AI forecast — hybrid routing — Change 4 of STEP 2)
│   ├── scenario-analysis/
│   ├── volatility-projection/
│   ├── expected-move/
│   ├── probability-tree/
│   ├── ai-consensus/
│   └── probability-engine/
│
├── supervisor/               (Layer 3: Supervisor AI — Change 3)
├── validator/                (Layer 4: Institutional Validation — Change 4)
├── self-correction/          (Layer 5: Continuous Learning — Change 12)
└── automation/               (Future — Change 16 — reserved)
    ├── execution/
    ├── risk/
    ├── position/
    └── broker/
```

## Agent contract

Every agent implements this contract:

```python
class Agent(Protocol):
    agent_id: str
    layer: str  # data-collection | raw-intelligence | decision-intelligence | supervisor | validator | self-correction | automation

    async def start(self, config: AgentConfig) -> None: ...
    async def stop(self) -> None: ...
    async def on_event(self, event: BusEvent) -> None: ...
```

## Agent file structure

```
agents/<layer>/<agent-name>/
├── README.md
├── pyproject.toml
├── src/<pkg>/
│   ├── __init__.py
│   ├── manifest.py        # agent manifest (id, layer, subscriptions, publications)
│   ├── config.py          # Zod-validated config schema
│   ├── types.py           # agent-specific types
│   └── agent.py           # the agent class
└── tests/
    ├── __init__.py
    └── test_agent.py
```

## Reporting to Supervisor (Change 3)

Every agent emits periodic `system:agent-heartbeat` events with the 10
health metrics (Change 17). The Supervisor subscribes to all heartbeats,
detects failures, triggers retries, and adjusts confidence weights.

## Raw vs Decision Intelligence (Change 2)

- **Raw Intelligence** agents publish facts only (e.g., `ta:indicator-computed`,
  `ta:signal-emitted`, `options:iv-updated`). Never conclusions.
- **Decision Intelligence** agents publish conclusions only (e.g.,
  `decision:regime-classified`, `decision:scenario-updated`, `forecast:trajectory-computed`).
  Never raw facts.

This separation is enforced by ESLint and reviewed in PRs.
''')

# Helper to scaffold an agent
def scaffold_agent(layer: str, slug: str, name: str, description: str,
                   subscribes: list[str], publishes: list[str],
                   plugin_deps: list[str] = None) -> None:
    base = f"agents/{layer}/{slug}"
    pkg_name = f"athena_x_agent_{layer.replace('-', '_')}_{slug.replace('-', '_')}"
    # Build a valid Python class name (must start with letter/underscore, alphanumeric only)
    def py_class(parts: list[str]) -> str:
        name = "".join(p.title() for p in parts)
        if name and name[0].isdigit():
            name = "_" + name
        return name + "Agent"
    def py_manifest(parts: list[str]) -> str:
        name = "".join(p.title() for p in parts)
        if name and name[0].isdigit():
            name = "_" + name
        return name + "Manifest"
    class_name = py_class(slug.split("-"))
    manifest_name = py_manifest(slug.split("-"))

    w(f"{base}/README.md", f'''
# {name}

> Layer: **{layer}**

{description}

## Event subscriptions

{chr(10).join(f"- `{s}`" for s in subscribes) if subscribes else "- (none — source agent)"}

## Event publications

{chr(10).join(f"- `{p}`" for p in publishes) if publishes else "- (none)"}

## Plugin dependencies

{chr(10).join(f"- `{p}`" for p in (plugin_deps or [])) if plugin_deps else "- (none)"}

## Implementation status

- [x] Scaffold
- [ ] Implementation (STEP 4)
- [ ] Tests (STEP 4)
''')

    deps_list = ['"athena-x-runtime-event-bus"', '"athena-x-runtime-logger"', '"athena-x-runtime-health-monitor"']
    if plugin_deps:
        for pd in plugin_deps:
            pkg = pd.replace(".", "-")
            deps_list.append(f'"athena-x-plugin-{pkg}"')
    deps_str = "\n".join(f"    {d}," for d in deps_list)

    w(f"{base}/pyproject.toml", f'''
[project]
name = "{pkg_name}"
version = "0.1.0"
description = "{name} — {layer} agent for ATHENA-X"
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

    subs_str = "\n".join(f'        "{s}",' for s in subscribes) or "        # source agent — no subscriptions"
    pubs_str = "\n".join(f'        "{p}",' for p in publishes) or "        # sink agent — no publications"
    plugins_str = "\n".join(f'        "{p}",' for p in (plugin_deps or [])) or "        # no plugin dependencies"

    w(f"{base}/src/{pkg_name}/manifest.py", f'''
"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class {manifest_name}:
    """Manifest for the {name}."""
    agent_id: str = "{layer}.{slug}"
    name: str = "{name}"
    layer: str = "{layer}"
    description: str = "{description}"
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

    w(f"{base}/src/{pkg_name}/config.py", f'''
"""Configuration for {name}."""
from __future__ import annotations
from pydantic import BaseModel


class {class_name[:-5]}Config(BaseModel):
    """Instance configuration. Add fields as needed in STEP 4."""
    enabled: bool = True
''')

    w(f"{base}/src/{pkg_name}/types.py", f'"""Types for {name}."""\nfrom __future__ import annotations\n')

    w(f"{base}/src/{pkg_name}/agent.py", f'''
"""{name} — agent implementation."""
from __future__ import annotations


class {class_name}:
    """
    {name}.

    Layer: {layer}

    Implementation comes in STEP 4 per the order in
    docs/architecture/implementation-order.md.
    """

    agent_id = "{layer}.{slug}"
    layer = "{layer}"

    def __init__(self, config):
        self.config = config
''')

    w(f"{base}/tests/__init__.py", "")
    w(f"{base}/tests/test_agent.py", f'"""Tests for {name}."""\n')


# === Data Collection (3 agents) ===
scaffold_agent(
    "data-collection", "collection-agent", "Data Collection Agent",
    "Pulls data from providers (Yahoo → Finnhub → Polygon → FlashAlpha → FRED → AlphaVantage failover chain). "
    "Normalizes timestamps. Writes raw payloads to raw_market_data schema.",
    subscribes=[],  # source
    publishes=["market:quote-updated", "market:trade-printed", "market:level2-updated",
               "market:bar-closed", "market:provider-failed-over"],
    plugin_deps=[],
)

scaffold_agent(
    "data-collection", "validation-agent", "Data Validation Agent",
    "Removes duplicates. Detects missing data. Computes data quality scores. "
    "Performs cross-provider validation. Rejects low-quality data.",
    subscribes=["market:quote-updated", "market:trade-printed", "market:bar-closed"],
    publishes=["system:provider-health-updated"],
    plugin_deps=[],
)

scaffold_agent(
    "data-collection", "standardization-agent", "Data Standardization Agent",
    "Maps provider-specific schemas to canonical ATHENA-X schema. Normalizes units. "
    "Writes validated, standardized data to processed_market_data schema. "
    "ONLY writer to processed_market_data.",
    subscribes=["market:quote-updated"],
    publishes=[],
    plugin_deps=[],
)

# === Raw Intelligence: Technical Analysis (23 agents — Change 6) ===
TA_AGENTS = [
    ("multi-timeframe", "Multi-Timeframe AI", "Analyzes trend alignment across 9 timeframes (Monthly→1M).",
     ["ta:indicator-computed"], ["ta:signal-emitted"], []),
    ("trend", "Trend AI", "Detects trend direction and strength using ADX + price action.",
     ["market:bar-closed"], ["ta:signal-emitted", "ta:level-identified"], ["indicators.adx"]),
    ("candlestick", "Candlestick AI", "Recognizes candlestick patterns (doji, hammer, engulfing, etc.).",
     ["market:bar-closed"], ["ta:signal-emitted"], ["patterns.candlestick"]),
    ("ema", "EMA AI", "Computes EMA values and detects crossovers.",
     ["market:bar-closed"], ["ta:indicator-computed", "ta:signal-emitted"], ["indicators.ema"]),
    ("sma", "SMA AI", "Computes SMA values and detects crossovers.",
     ["market:bar-closed"], ["ta:indicator-computed", "ta:signal-emitted"], ["indicators.sma"]),
    ("vwap", "VWAP AI", "Computes VWAP and detects deviations.",
     ["market:bar-closed"], ["ta:indicator-computed", "ta:signal-emitted"], ["indicators.vwap"]),
    ("rsi", "RSI AI", "Computes RSI and detects overbought/oversold conditions.",
     ["market:bar-closed"], ["ta:indicator-computed", "ta:signal-emitted"], ["indicators.rsi"]),
    ("macd", "MACD AI", "Computes MACD and detects bullish/bearish crossovers.",
     ["market:bar-closed"], ["ta:indicator-computed", "ta:signal-emitted"], ["indicators.macd"]),
    ("adx", "ADX AI", "Computes ADX and detects trend strength.",
     ["market:bar-closed"], ["ta:indicator-computed", "ta:signal-emitted"], ["indicators.adx"]),
    ("atr", "ATR AI", "Computes ATR for volatility measurement.",
     ["market:bar-closed"], ["ta:indicator-computed"], ["indicators.atr"]),
    ("bollinger", "Bollinger AI", "Computes Bollinger Bands and detects squeeze/expansion.",
     ["market:bar-closed"], ["ta:indicator-computed", "ta:signal-emitted"], ["indicators.bollinger"]),
    ("fibonacci", "Fibonacci AI", "Identifies Fibonacci retracement levels.",
     ["market:bar-closed"], ["ta:level-identified", "ta:signal-emitted"], ["indicators.fibonacci"]),
    ("elliott-wave", "Elliott Wave AI", "Analyzes Elliott Wave patterns.",
     ["market:bar-closed"], ["ta:signal-emitted"], ["patterns.elliott-wave"]),
    ("wyckoff", "Wyckoff AI", "Detects Wyckoff accumulation/distribution phases.",
     ["market:bar-closed"], ["ta:signal-emitted"], ["patterns.wyckoff"]),
    ("chan-theory", "Chan Theory AI", "缠论分析 (Bi/Duan/Zhongshu detection).",
     ["market:bar-closed"], ["ta:signal-emitted"], ["patterns.chan-theory"]),
    ("volume-profile", "Volume Profile AI", "Computes POC/VAH/VAL and volume distribution.",
     ["market:bar-closed"], ["ta:level-identified", "ta:signal-emitted"], ["patterns.volume-profile"]),
    ("volume-price", "Volume Price AI", "Analyzes volume-price relationships.",
     ["market:bar-closed"], ["ta:signal-emitted"], ["indicators.obv"]),
    ("support-resistance", "Support/Resistance AI", "Identifies key support and resistance levels.",
     ["market:bar-closed"], ["ta:level-identified"], []),
    ("liquidity", "Liquidity AI", "Detects liquidity pools and liquidity voids.",
     ["market:bar-closed"], ["ta:level-identified"], []),
    ("smart-money", "Smart Money AI", "Detects order blocks, FVGs, and smart money footprints.",
     ["market:bar-closed"], ["ta:signal-emitted"], ["patterns.smart-money"]),
    ("escape-top", "Escape Top AI", "Detects breakout-from-consolidation patterns.",
     ["market:bar-closed"], ["ta:signal-emitted"], []),
    ("entry", "Entry AI", "Identifies high-probability entry points.",
     ["ta:signal-emitted", "ta:level-identified"], ["ta:signal-emitted"], []),
    ("pull-up-pattern", "Pull-Up Pattern AI", "Detects pull-up continuation patterns.",
     ["market:bar-closed"], ["ta:signal-emitted"], []),
]

for slug, name, desc, subs, pubs, plugins in TA_AGENTS:
    scaffold_agent("raw-intelligence/technical-analysis", slug, name, desc, subs, pubs, plugins)

# === Raw Intelligence: Options (15 agents — Change 7) ===
OPTIONS_AGENTS = [
    ("greeks", "Greeks AI", "Computes option Greeks (delta, gamma, theta, vega, rho).",
     ["market:quote-updated"], ["options:greeks-computed"], ["options.greeks"]),
    ("iv", "IV AI", "Computes implied volatility via Brent's method.",
     ["market:quote-updated"], ["options:iv-updated"], ["options.iv"]),
    ("iv-crush", "IV Crush AI", "Detects IV crush events post-earnings.",
     ["options:iv-updated"], ["options:iv-updated"], []),
    ("iv-rank", "IV Rank AI", "Computes IV rank and IV percentile.",
     ["options:iv-updated"], ["options:iv-updated"], []),
    ("skew", "Skew AI", "Analyzes IV skew (risk reversal, butterfly).",
     ["options:iv-updated"], ["options:iv-updated"], ["options.skew"]),
    ("option-flow", "Option Flow AI", "Detects unusual options activity.",
     ["market:trade-printed"], ["options:unusual-activity"], []),
    ("dealer-position", "Dealer Position AI", "Estimates dealer positioning.",
     ["options:greeks-computed"], ["options:greeks-computed"], []),
    ("gamma-exposure", "Gamma Exposure AI", "Computes GEX and gamma flip level.",
     ["options:greeks-computed"], ["options:gamma-exposure-updated"], ["options.gamma-exposure"]),
    ("gamma-flip", "Gamma Flip AI", "Detects gamma flip transitions.",
     ["options:gamma-exposure-updated"], ["options:gamma-exposure-updated"], []),
    ("max-pain", "Max Pain AI", "Computes max pain for each expiry.",
     ["market:quote-updated"], ["options:max-pain-updated"], ["options.max-pain"]),
    ("open-interest", "Open Interest AI", "Analyzes OI changes and concentrations.",
     ["market:quote-updated"], ["options:chain-refreshed"], []),
    ("0dte", "0DTE AI", "Specialized analysis for 0-days-to-expiry options.",
     ["options:chain-refreshed"], ["options:unusual-activity"], []),
    ("volatility-surface", "Volatility Surface AI", "Builds 3D IV surface across strikes/expiries.",
     ["options:iv-updated"], ["options:iv-updated"], ["options.volatility-surface"]),
    ("expected-move", "Expected Move AI", "Computes expected move from options market.",
     ["options:iv-updated"], ["decision:expected-move-updated"], []),
    ("probability-of-profit", "Probability of Profit AI", "Computes PoP for option strategies.",
     ["options:iv-updated"], ["probability:profit-scored"], []),
]

for slug, name, desc, subs, pubs, plugins in OPTIONS_AGENTS:
    scaffold_agent("raw-intelligence/options", slug, name, desc, subs, pubs, plugins)

# === Raw Intelligence: News + Macro ===
scaffold_agent(
    "raw-intelligence", "news-agent", "News Agent",
    "Ingests news from RSS + provider APIs. Runs HuggingFace FinBERT for sentiment + impact.",
    subscribes=[],
    publishes=["news:headline-received", "news:sentiment-scored", "news:impact-classified", "news:entity-mentioned"],
    plugin_deps=[],
)

scaffold_agent(
    "raw-intelligence", "macro-agent", "Macro Agent",
    "Ingests macro indicators from FRED (US), ECB (EU), PBoC (CN), BoJ (JP), ONS (UK).",
    subscribes=[],
    publishes=["macro:indicator-released", "macro:yield-curve-updated", "macro:fx-rate-updated", "macro:commodity-updated"],
    plugin_deps=[],
)

# === Raw Intelligence: Cross-Market (20 agents — Change 8) ===
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
        "raw-intelligence/cross-market", slug, f"{label} Cross-Market Agent",
        f"{desc}. Feeds SPY Intelligence aggregator.",
        subscribes=["market:quote-updated"],
        publishes=["cross-market:symbol-state-updated"],
        plugin_deps=[],
    )

# Cross-market SPY Intelligence aggregator
scaffold_agent(
    "raw-intelligence/cross-market", "spy-intelligence-aggregator", "SPY Intelligence Aggregator",
    "Subscribes to all 20 cross-market agents. Aggregates their state into a unified "
    "SPY Intelligence view. This is the single source of truth for SPY context.",
    subscribes=["cross-market:symbol-state-updated"],
    publishes=["cross-market:spy-intelligence-updated"],
    plugin_deps=[],
)

# === Decision Intelligence (9 agents — Changes 5, 9, 10) ===
DECISION_AGENTS = [
    ("market-regime", "Market Regime AI",
     "Classifies market regime (Change 9): trending/ranging/breakout/mean-reversion/high-vol/low-vol/news-driven/option-driven/dealer-controlled. "
     "No indicator is interpreted without regime context.",
     ["ta:signal-emitted", "options:iv-updated", "news:impact-classified", "macro:indicator-released"],
     ["decision:regime-classified"], []),
    ("timeframe-sync", "Timeframe Synchronization AI",
     "Computes multi-timeframe alignment score (Change 10): Monthly → Weekly → Daily → 4H → 1H → 30M → 15M → 5M → 1M → Alignment Score.",
     ["ta:indicator-computed"],
     ["decision:timeframe-alignment-updated"], []),
    ("forecast", "AI Forecast Engine",
     "Hybrid AI forecast ensemble (Change 4 of STEP 2). LSTM/Transformer/TabPFN/XGBoost/CatBoost/LightGBM-large → Python GPU; "
     "LightGBM-small/RF/Logistic → Browser ONNX. LSTM NEVER runs in browser.",
     ["market:bar-closed", "decision:regime-classified", "learning:weight-adjusted"],
     ["forecast:trajectory-computed", "forecast:catalyst-detected"], []),
    ("scenario-analysis", "Scenario Analysis AI",
     "Computes Bull/Base/Bear scenario probabilities based on regime + forecast + cross-market.",
     ["forecast:trajectory-computed", "decision:regime-classified"],
     ["decision:scenario-updated"], []),
    ("volatility-projection", "Volatility Projection AI",
     "Projects forward volatility using GARCH + ATR + IV term structure.",
     ["ta:indicator-computed", "options:iv-updated"],
     ["decision:volatility-projected"], []),
    ("expected-move", "Expected Move AI",
     "Computes expected move (Decision Intelligence layer) — combines options-implied + historical + ATR-based.",
     ["decision:volatility-projected", "options:iv-updated"],
     ["decision:expected-move-updated"], []),
    ("probability-tree", "Probability Tree AI",
     "Builds a probability tree of future states (price paths + regime transitions).",
     ["decision:regime-classified", "forecast:trajectory-computed"],
     ["decision:probability-tree-updated"], []),
    ("ai-consensus", "AI Consensus AI",
     "Aggregates all decision agents into a single consensus view per symbol.",
     ["decision:regime-classified", "decision:scenario-updated", "decision:expected-move-updated",
      "decision:probability-tree-updated", "decision:timeframe-alignment-updated"],
     ["decision:ai-consensus-updated"], []),
    ("probability-engine", "Probability Engine",
     "Monte Carlo simulation engine. Configurable DTE, simulations count, threshold.",
     ["decision:volatility-projected", "forecast:trajectory-computed"],
     ["probability:simulation-run", "probability:profit-scored", "probability:strategy-matrix-updated"], []),
]

for slug, name, desc, subs, pubs, plugins in DECISION_AGENTS:
    scaffold_agent("decision-intelligence", slug, name, desc, subs, pubs, plugins)

# === Supervisor (Change 3) ===
scaffold_agent(
    "supervisor", "supervisor-agent", "Supervisor AI",
    "Every AI agent reports to the Supervisor (Change 3). Detects conflicting signals, "
    "checks stale data, detects failing agents, triggers retries, performs confidence weighting, "
    "delegates report generation, runs self-learning, and tracks performance statistics.",
    subscribes=["*"],  # subscribes to ALL events
    publishes=["supervisor:conflict-detected", "supervisor:agent-failing",
               "supervisor:retry-requested", "supervisor:confidence-adjusted"],
    plugin_deps=[],
)

# === Validator (Change 4) ===
scaffold_agent(
    "validator", "validation-agent", "Institutional Validation Agent",
    "Institutional Validation Layer (Change 4). Before any report reaches the dashboard: "
    "confidence ≥ threshold, evidence ≥ minimum, data freshness within window, source count ≥ minimum, "
    "agreement score ≥ threshold. Publishes report-approved or report-rejected.",
    subscribes=["report:generation-completed"],
    publishes=["validator:report-approved", "validator:report-rejected",
               "validator:backtest-run", "validator:calibration-updated"],
    plugin_deps=[],
)

# === Self-Correction (Change 12) ===
scaffold_agent(
    "self-correction", "self-correction-agent", "Self-Correction Agent",
    "Continuous learning engine (Change 12). Pipeline: prediction → market outcome → compare → error → "
    "weight adjustment → improve model. Every prediction is scored. Adjusts model_weights table.",
    subscribes=["forecast:trajectory-computed", "market:bar-closed"],
    publishes=["learning:prediction-scored", "learning:weight-adjusted"],
    plugin_deps=[],
)

# === Automation (Change 16 — reserved) ===
AUTO_AGENTS = [
    ("execution", "Execution AI", "Order placement (future). Disabled by feature flag."),
    ("risk", "Risk AI", "Pre-trade risk checks (future). Disabled by feature flag."),
    ("position", "Position AI", "Position management (future). Disabled by feature flag."),
    ("broker", "Broker API Adapter", "Broker API integration (IBKR, Alpaca). Disabled by feature flag."),
]

for slug, name, desc in AUTO_AGENTS:
    scaffold_agent(
        "automation", slug, name, desc + " Reserved architecture per Change 16.",
        subscribes=[],
        publishes=[],
        plugin_deps=[],
    )

print(f"\n✅ Part 2 complete: {FILES_WRITTEN} files written under {ROOT}")
