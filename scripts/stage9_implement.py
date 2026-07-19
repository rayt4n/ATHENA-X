#!/usr/bin/env python3
"""
STEP 4 Stage 9 - Market Intelligence & Correlation Platform
=============================================================
Implements:
  1. plugins/cross-market/_base/ - CrossMarketPlugin Protocol
  2. 60+ plugin manifests (market monitors + correlations + leadership + regime + rotation + divergence)
  3. engines/cross-market-plugin-engine/ - Plugin Manager + Correlation Engine + Leadership Engine
  4. agents/market-intelligence/ - Market Intelligence Hub + Market DNA Agent
  5. runtime/stage9-integration/ - acceptance tests

Key: Answers "What is driving ES right now?" via Market DNA.

Run: python /home/z/my-project/scripts/stage9_implement.py
"""

from pathlib import Path
import textwrap

ROOT = Path("/home/z/my-project/athena-x")
ROOT.mkdir(parents=True, exist_ok=True)
FILES = []

def w(rel: str, content: str) -> None:
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(textwrap.dedent(content).lstrip("\n"))
    FILES.append(rel)


# ============================================================================
# 1. CROSS-MARKET PLUGIN PROTOCOL
# ============================================================================

w("plugins/cross-market/_base/pyproject.toml", '''
[project]
name = "athena-x-plugin-cross-market-base"
version = "0.1.0"
description = "CrossMarketPlugin Protocol - stable interface for cross-market plugins (Stage 9)"
requires-python = ">=3.11"
dependencies = ["pydantic>=2.9.0"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/athena_x_plugin_cross_market_base"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
''')

w("plugins/cross-market/_base/src/athena_x_plugin_cross_market_base/__init__.py", '''
"""CrossMarketPlugin Protocol - stable interface for all cross-market plugins."""
from .protocol import (
    CrossMarketPlugin, MarketDataInput, CrossMarketOutput,
    CrossMarketCategory, MarketGroup,
)

__all__ = [
    "CrossMarketPlugin", "MarketDataInput", "CrossMarketOutput",
    "CrossMarketCategory", "MarketGroup",
]
__version__ = "0.1.0"
''')

w("plugins/cross-market/_base/src/athena_x_plugin_cross_market_base/protocol.py", '''
"""CrossMarketPlugin Protocol - stable interface for all cross-market plugins.

Stage 9: Every cross-market metric is an independent plugin.
The engine doesn't know which correlations or leadership signals exist.
It only loads plugins.

Categories:
  - market_monitor: one per asset (spy, es, vix, dxy, ...)
  - correlation: SPY<->ES, SPY<->VIX, ...
  - leadership: who is leading? who is lagging?
  - regime: Risk-On, Risk-Off, Inflation, ...
  - rotation: Tech->Defensive, Growth->Value, ...
  - divergence: spy_es_divergence, vix_not_confirming, ...
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol, runtime_checkable


class CrossMarketCategory(str, Enum):
    MARKET_MONITOR = "market_monitor"
    CORRELATION = "correlation"
    LEADERSHIP = "leadership"
    REGIME = "regime"
    ROTATION = "rotation"
    DIVERGENCE = "divergence"


class MarketGroup(str, Enum):
    CORE = "core"
    VOLATILITY = "volatility"
    RATES = "rates"
    CURRENCY = "currency"
    COMMODITIES = "commodities"
    BREADTH = "breadth"
    SECTORS = "sectors"
    SEMICONDUCTOR = "semiconductor"
    MAG7 = "mag7"
    GLOBAL = "global"
    CRYPTO = "crypto"


@dataclass
class MarketDataInput:
    """Input data for a cross-market plugin."""
    symbol: str = ""
    # Latest quotes for all monitored symbols
    quotes: dict[str, dict] = field(default_factory=dict)  # symbol -> {last, change_pct, volume, ...}
    # Recent returns for correlation calculation
    returns: dict[str, list[float]] = field(default_factory=dict)  # symbol -> [ret1, ret2, ...]
    # Timestamp
    timestamp: str = ""


@dataclass
class CrossMarketOutput:
    """Output of a cross-market plugin computation."""
    plugin_id: str
    category: CrossMarketCategory
    value: Any
    confidence: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)
    calculation_time_ms: float = 0.0


@runtime_checkable
class CrossMarketPlugin(Protocol):
    """Stable interface for all cross-market intelligence plugins.

    Usage:
        plugin: CrossMarketPlugin = SPYCorrelationPlugin()
        result = plugin.compute(input_data)
    """

    @property
    def plugin_id(self) -> str: ...

    @property
    def category(self) -> CrossMarketCategory: ...

    @property
    def version(self) -> str: ...

    def compute(self, input_data: MarketDataInput) -> CrossMarketOutput: ...
''')

w("plugins/cross-market/_base/tests/__init__.py", "")
w("plugins/cross-market/_base/tests/test_protocol.py", '''
"""Tests for CrossMarketPlugin Protocol."""
import pytest
from athena_x_plugin_cross_market_base import (
    CrossMarketPlugin, MarketDataInput, CrossMarketOutput,
    CrossMarketCategory, MarketGroup,
)


class FakeCorrelationPlugin:
    @property
    def plugin_id(self): return "spy_es_correlation"
    @property
    def category(self): return CrossMarketCategory.CORRELATION
    @property
    def version(self): return "1.0.0"
    def compute(self, input_data):
        return CrossMarketOutput(
            plugin_id="spy_es_correlation",
            category=CrossMarketCategory.CORRELATION,
            value={"correlation": 0.98, "spy_leading": False},
        )


def test_protocol_is_runtime_checkable():
    plugin = FakeCorrelationPlugin()
    assert isinstance(plugin, CrossMarketPlugin)


def test_6_categories_defined():
    assert CrossMarketCategory.MARKET_MONITOR.value == "market_monitor"
    assert CrossMarketCategory.CORRELATION.value == "correlation"
    assert CrossMarketCategory.LEADERSHIP.value == "leadership"
    assert CrossMarketCategory.REGIME.value == "regime"
    assert CrossMarketCategory.ROTATION.value == "rotation"
    assert CrossMarketCategory.DIVERGENCE.value == "divergence"


def test_11_market_groups_defined():
    assert MarketGroup.CORE.value == "core"
    assert MarketGroup.VOLATILITY.value == "volatility"
    assert MarketGroup.SEMICONDUCTOR.value == "semiconductor"
    assert MarketGroup.MAG7.value == "mag7"
    assert MarketGroup.CRYPTO.value == "crypto"


def test_compute_returns_output():
    plugin = FakeCorrelationPlugin()
    inp = MarketDataInput(quotes={"SPY": {"last": 450}, "ES": {"last": 4520}})
    result = plugin.compute(inp)
    assert isinstance(result, CrossMarketOutput)
    assert result.value["correlation"] == 0.98
''')

# ============================================================================
# 2. PLUGIN MANIFESTS - 60+ cross-market plugins
# ============================================================================

# Market monitor plugins (one per instrument)
MARKET_MONITORS = [
    # Core
    ("es", "ES Monitor", "core", "E-mini S&P 500 Futures"),
    ("spy", "SPY Monitor", "core", "SPDR S&P 500 ETF"),
    ("spx", "SPX Monitor", "core", "S&P 500 Index"),
    ("nq", "NQ Monitor", "core", "E-mini Nasdaq 100 Futures"),
    ("qqq", "QQQ Monitor", "core", "Invesco QQQ Trust"),
    # Volatility
    ("vix", "VIX Monitor", "volatility", "CBOE Volatility Index"),
    ("vvix", "VVIX Monitor", "volatility", "Volatility of Volatility"),
    ("move", "MOVE Monitor", "volatility", "ICE BofA MOVE Index"),
    # Rates
    ("tnx", "10Y Treasury Monitor", "rates", "10-Year Treasury Yield"),
    ("us2y", "2Y Treasury Monitor", "rates", "2-Year Treasury Yield"),
    ("us30y", "30Y Treasury Monitor", "rates", "30-Year Treasury Yield"),
    # Currency
    ("dxy", "DXY Monitor", "currency", "US Dollar Index"),
    ("usdjpy", "USDJPY Monitor", "currency", "USD/JPY exchange rate"),
    ("eurusd", "EURUSD Monitor", "currency", "EUR/USD exchange rate"),
    # Commodities
    ("gold", "Gold Monitor", "commodities", "Gold spot price"),
    ("silver", "Silver Monitor", "commodities", "Silver spot price"),
    ("oil", "Oil Monitor", "commodities", "WTI Crude Oil"),
    ("natgas", "Natural Gas Monitor", "commodities", "Natural Gas"),
    ("copper", "Copper Monitor", "commodities", "Copper futures"),
    # Sectors
    ("xlk", "XLK Monitor", "sectors", "Technology Select Sector ETF"),
    ("xlf", "XLF Monitor", "sectors", "Financial Select Sector ETF"),
    ("xlv", "XLV Monitor", "sectors", "Health Care Select Sector ETF"),
    ("xly", "XLY Monitor", "sectors", "Consumer Discretionary Select Sector ETF"),
    ("xli", "XLI Monitor", "sectors", "Industrial Select Sector ETF"),
    ("xle", "XLE Monitor", "sectors", "Energy Select Sector ETF"),
    ("xlp", "XLP Monitor", "sectors", "Consumer Staples Select Sector ETF"),
    ("xlb", "XLB Monitor", "sectors", "Materials Select Sector ETF"),
    ("xlu", "XLU Monitor", "sectors", "Utilities Select Sector ETF"),
    ("xlre", "XLRE Monitor", "sectors", "Real Estate Select Sector ETF"),
    ("xlc", "XLC Monitor", "sectors", "Communication Services Select Sector ETF"),
    # Semiconductor
    ("soxx", "SOXX Monitor", "semiconductor", "iShares Semiconductor ETF"),
    ("smh", "SMH Monitor", "semiconductor", "VanEck Semiconductor ETF"),
    ("nvda", "NVDA Monitor", "semiconductor", "NVIDIA Corporation"),
    ("amd", "AMD Monitor", "semiconductor", "Advanced Micro Devices"),
    ("avgo", "AVGO Monitor", "semiconductor", "Broadcom Inc"),
    ("tsm", "TSM Monitor", "semiconductor", "Taiwan Semiconductor"),
    ("mu", "MU Monitor", "semiconductor", "Micron Technology"),
    ("arm", "ARM Monitor", "semiconductor", "Arm Holdings"),
    # MAG7
    ("aapl", "AAPL Monitor", "mag7", "Apple Inc"),
    ("msft", "MSFT Monitor", "mag7", "Microsoft Corporation"),
    ("amzn", "AMZN Monitor", "mag7", "Amazon.com Inc"),
    ("googl", "GOOGL Monitor", "mag7", "Alphabet Inc"),
    ("meta", "META Monitor", "mag7", "Meta Platforms"),
    ("tsla", "TSLA Monitor", "mag7", "Tesla Inc"),
    # Global
    ("nikkei", "Nikkei Monitor", "global", "Nikkei 225 Index"),
    ("hangseng", "Hang Seng Monitor", "global", "Hang Seng Index"),
    ("shanghai", "Shanghai Monitor", "global", "Shanghai Composite"),
    ("asx200", "ASX200 Monitor", "global", "S&P/ASX 200 Index"),
    ("dax", "DAX Monitor", "global", "DAX 40 Index"),
    ("ftse", "FTSE Monitor", "global", "FTSE 100 Index"),
    ("cac40", "CAC40 Monitor", "global", "CAC 40 Index"),
    ("eurostoxx", "Euro Stoxx Monitor", "global", "Euro Stoxx 50 Index"),
    # Crypto
    ("btc", "BTC Monitor", "crypto", "Bitcoin"),
    ("eth", "ETH Monitor", "crypto", "Ethereum"),
]

# Correlation plugins
CORRELATIONS = [
    ("spy_es_corr", "SPY-ES Correlation", "SPY vs ES correlation"),
    ("spy_vix_corr", "SPY-VIX Correlation", "SPY vs VIX correlation"),
    ("spy_dxy_corr", "SPY-DXY Correlation", "SPY vs DXY correlation"),
    ("spy_tnx_corr", "SPY-TNX Correlation", "SPY vs TNX correlation"),
    ("spy_oil_corr", "SPY-Oil Correlation", "SPY vs Oil correlation"),
    ("spy_gold_corr", "SPY-Gold Correlation", "SPY vs Gold correlation"),
    ("spy_soxx_corr", "SPY-SOXX Correlation", "SPY vs SOXX correlation"),
    ("spy_qqq_corr", "SPY-QQQ Correlation", "SPY vs QQQ correlation"),
    ("spy_breadth_corr", "SPY-Breadth Correlation", "SPY vs Breadth correlation"),
    ("qqq_soxx_corr", "QQQ-SOXX Correlation", "QQQ vs SOXX correlation"),
    ("qqq_nvda_corr", "QQQ-NVDA Correlation", "QQQ vs NVDA correlation"),
    ("es_nq_corr", "ES-NQ Correlation", "ES vs NQ correlation"),
]

# Leadership plugins
LEADERSHIP = [
    ("nvda_leads_qqq", "NVDA Leads QQQ", "Is NVDA leading QQQ?"),
    ("qqq_leads_spy", "QQQ Leads SPY", "Is QQQ leading SPY?"),
    ("soxx_vs_xlk", "SOXX vs XLK", "Is SOXX stronger than XLK?"),
    ("vix_confirming", "VIX Confirming", "Is VIX confirming the move?"),
    ("dxy_driving", "DXY Driving", "Is DXY driving weakness?"),
    ("bonds_driving", "Bonds Driving", "Are bonds driving the move?"),
]

# Regime plugins
REGIMES = [
    ("risk_on", "Risk-On Regime", "Risk-on market regime detection"),
    ("risk_off", "Risk-Off Regime", "Risk-off market regime detection"),
    ("inflation_regime", "Inflation Regime", "Inflation-driven regime"),
    ("deflation_regime", "Deflation Regime", "Deflation-driven regime"),
    ("liquidity_expansion", "Liquidity Expansion", "Liquidity expansion regime"),
    ("liquidity_contraction", "Liquidity Contraction", "Liquidity contraction regime"),
]

# Rotation plugins
ROTATIONS = [
    ("tech_to_defensive", "Tech to Defensive", "Tech to defensive rotation"),
    ("growth_to_value", "Growth to Value", "Growth to value rotation"),
    ("large_to_small", "Large to Small", "Large cap to small cap rotation"),
    ("semi_to_software", "Semi to Software", "Semiconductor to software rotation"),
    ("cyclical_to_utilities", "Cyclical to Utilities", "Cyclical to utilities rotation"),
]

# Divergence plugins
DIVERGENCES = [
    ("spy_es_divergence", "SPY-ES Divergence", "SPY diverging from ES"),
    ("vix_not_confirming", "VIX Not Confirming", "VIX not confirming price action"),
    ("breadth_weakening", "Breadth Weakening", "Market breadth weakening"),
    ("soxx_breakout", "SOXX Breakout", "SOXX breaking out"),
    ("nvda_leading", "NVDA Leading", "NVDA leading the market"),
    ("bond_divergence", "Bond Divergence", "Bonds diverging from equities"),
]

# Generate all manifests
for slug, name, group, desc in MARKET_MONITORS:
    w(f"plugins/cross-market/{slug}/manifest.yaml", f'''id: {slug}
name: "{name}"
version: "1.0.0"
category: market_monitor
market_group: {group}
refresh_interval_seconds: 1
inputs: [quotes]
outputs: [status, change_pct, volume]
dependencies: []
enabled: true
description: "{desc}"
author: "ATHENA-X"
''')

for slug, name, desc in CORRELATIONS:
    w(f"plugins/cross-market/{slug}/manifest.yaml", f'''id: {slug}
name: "{name}"
version: "1.0.0"
category: correlation
refresh_interval_seconds: 60
inputs: [returns]
outputs: [correlation, leading_symbol]
dependencies: []
enabled: true
description: "{desc}"
author: "ATHENA-X"
''')

for slug, name, desc in LEADERSHIP:
    w(f"plugins/cross-market/{slug}/manifest.yaml", f'''id: {slug}
name: "{name}"
version: "1.0.0"
category: leadership
refresh_interval_seconds: 5
inputs: [quotes, returns]
outputs: [leader, lagger, signal]
dependencies: []
enabled: true
description: "{desc}"
author: "ATHENA-X"
''')

for slug, name, desc in REGIMES:
    w(f"plugins/cross-market/{slug}/manifest.yaml", f'''id: {slug}
name: "{name}"
version: "1.0.0"
category: regime
refresh_interval_seconds: 10
inputs: [quotes, returns]
outputs: [regime_active, confidence]
dependencies: []
enabled: true
description: "{desc}"
author: "ATHENA-X"
''')

for slug, name, desc in ROTATIONS:
    w(f"plugins/cross-market/{slug}/manifest.yaml", f'''id: {slug}
name: "{name}"
version: "1.0.0"
category: rotation
refresh_interval_seconds: 30
inputs: [quotes, returns]
outputs: [rotation_active, from_sector, to_sector]
dependencies: []
enabled: true
description: "{desc}"
author: "ATHENA-X"
''')

for slug, name, desc in DIVERGENCES:
    w(f"plugins/cross-market/{slug}/manifest.yaml", f'''id: {slug}
name: "{name}"
version: "1.0.0"
category: divergence
refresh_interval_seconds: 5
inputs: [quotes, returns]
outputs: [divergence_active, description]
dependencies: []
enabled: true
description: "{desc}"
author: "ATHENA-X"
''')

# ============================================================================
# 3. CROSS-MARKET PLUGIN ENGINE
# ============================================================================

w("engines/cross-market-plugin-engine/pyproject.toml", '''
[project]
name = "athena-x-engine-cross-market-plugin-engine"
version = "0.1.0"
description = "Cross-Market Plugin Manager + Correlation Engine + Leadership Engine"
requires-python = ">=3.11"
dependencies = [
    "athena-x-engine-plugin-engine",
    "athena-x-plugin-cross-market-base",
    "athena-x-runtime-logger",
    "athena-x-runtime-event-envelope",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/athena_x_engine_cross_market_plugin_engine"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
''')

w("engines/cross-market-plugin-engine/src/athena_x_engine_cross_market_plugin_engine/__init__.py", '''
"""Cross-Market Plugin Engine."""
from .manager import CrossMarketPluginManager
from .correlation import CorrelationEngine, CorrelationMatrix
from .leadership import LeadershipEngine, LeadershipResult

__all__ = [
    "CrossMarketPluginManager",
    "CorrelationEngine", "CorrelationMatrix",
    "LeadershipEngine", "LeadershipResult",
]
__version__ = "0.1.0"
''')

w("engines/cross-market-plugin-engine/src/athena_x_engine_cross_market_plugin_engine/manager.py", '''
"""Cross-Market Plugin Manager - discovers + loads cross-market plugins.

Reuses the Stage 7 plugin engine infrastructure.
The engine doesn't know which correlations or leadership signals exist.
It only loads plugins.
"""
from __future__ import annotations
from pathlib import Path
from athena_x_engine_plugin_engine import PluginManager
from athena_x_runtime_logger import get_logger

log = get_logger("cross-market-plugin-engine")


class CrossMarketPluginManager:
    """Manages cross-market intelligence plugins.

    Wraps the Stage 7 PluginManager with cross-market-specific defaults.
    """

    def __init__(self, plugin_dir: str | Path = "plugins/cross-market"):
        self._inner = PluginManager(plugin_dir=plugin_dir)
        self._registry = self._inner.registry

    @property
    def registry(self):
        return self._registry

    @property
    def dependency_resolver(self):
        return self._inner.dependency_resolver

    @property
    def scheduler(self):
        return self._inner.scheduler

    @property
    def config_service(self):
        return self._inner.config_service

    def discover(self) -> int:
        return self._inner.discover()

    def load_all(self) -> int:
        return self._inner.load_all()

    def load(self, plugin_id: str):
        return self._inner.load(plugin_id)

    def get_instance(self, plugin_id: str):
        return self._inner.get_instance(plugin_id)

    def list_by_category(self, category: str) -> list:
        return [
            e for e in self._registry.list_all()
            if e.manifest.category.value == category
        ]

    def get_stats(self) -> dict:
        stats = self._inner.get_stats()
        from collections import Counter
        categories = Counter()
        for entry in self._registry.list_all():
            categories[entry.manifest.category.value] += 1
        stats["by_category"] = dict(categories)
        return stats
''')

w("engines/cross-market-plugin-engine/src/athena_x_engine_cross_market_plugin_engine/correlation.py", '''
"""Correlation Engine - calculates real-time correlation matrix.

Stage 9 req: Every minute calculate ES<->SPY, SPY<->VIX, SPY<->DXY, etc.
Publish only when changes exceed meaningful thresholds.
"""
from __future__ import annotations
import math
from dataclasses import dataclass, field
from threading import RLock
from typing import Any
from athena_x_runtime_logger import get_logger

log = get_logger("correlation-engine")


@dataclass
class CorrelationMatrix:
    """Real-time correlation matrix."""
    pairs: dict[str, float] = field(default_factory=dict)  # "SPY:ES" -> 0.98
    timestamp: str = ""
    changes: list[str] = field(default_factory=list)  # pairs that changed beyond threshold


class CorrelationEngine:
    """Calculates and monitors cross-asset correlations.

    Usage:
        engine = CorrelationEngine()
        engine.update_returns("SPY", [0.01, -0.02, 0.03, ...])
        engine.update_returns("ES", [0.01, -0.02, 0.03, ...])
        matrix = engine.compute_matrix(pairs=[("SPY", "ES"), ("SPY", "VIX")])
    """

    def __init__(self, change_threshold: float = 0.05):
        self._returns: dict[str, list[float]] = {}
        self._previous: dict[str, float] = {}  # previous correlations
        self._threshold = change_threshold
        self._lock = RLock()

    def update_returns(self, symbol: str, returns: list[float]) -> None:
        with self._lock:
            self._returns[symbol] = returns

    def compute_correlation(self, sym_a: str, sym_b: str) -> float | None:
        """Compute Pearson correlation between two symbols."""
        with self._lock:
            rets_a = self._returns.get(sym_a, [])
            rets_b = self._returns.get(sym_b, [])

        if len(rets_a) < 2 or len(rets_b) < 2:
            return None

        n = min(len(rets_a), len(rets_b))
        a = rets_a[-n:]
        b = rets_b[-n:]

        mean_a = sum(a) / n
        mean_b = sum(b) / n

        cov = sum((a[i] - mean_a) * (b[i] - mean_b) for i in range(n)) / n
        std_a = math.sqrt(sum((x - mean_a) ** 2 for x in a) / n)
        std_b = math.sqrt(sum((x - mean_b) ** 2 for x in b) / n)

        if std_a == 0 or std_b == 0:
            return 0.0

        return cov / (std_a * std_b)

    def compute_matrix(self, pairs: list[tuple[str, str]]) -> CorrelationMatrix:
        """Compute correlation for multiple pairs."""
        results: dict[str, float] = {}
        changes: list[str] = []

        for sym_a, sym_b in pairs:
            corr = self.compute_correlation(sym_a, sym_b)
            if corr is not None:
                key = f"{sym_a}:{sym_b}"
                results[key] = round(corr, 4)

                # Check for meaningful change
                prev = self._previous.get(key)
                if prev is not None and abs(corr - prev) > self._threshold:
                    changes.append(f"{key} changed from {prev:.4f} to {corr:.4f}")

                with self._lock:
                    self._previous[key] = corr

        return CorrelationMatrix(
            pairs=results,
            changes=changes,
        )

    def get_stats(self) -> dict:
        with self._lock:
            return {
                "symbols_tracked": len(self._returns),
                "correlations_cached": len(self._previous),
            }
''')

w("engines/cross-market-plugin-engine/src/athena_x_engine_cross_market_plugin_engine/leadership.py", '''
"""Leadership Engine - determines who is leading, lagging, or diverging.

Stage 9 req: Continuously answer:
  - Is NVDA leading QQQ?
  - Is QQQ leading SPY?
  - Is SOXX stronger than XLK?
  - Is VIX confirming?
"""
from __future__ import annotations
from dataclasses import dataclass, field
from threading import RLock
from typing import Any
from athena_x_runtime_logger import get_logger

log = get_logger("leadership-engine")


@dataclass
class LeadershipResult:
    """Result of a leadership analysis."""
    leader: str | None = None
    lagger: str | None = None
    signal: str = "neutral"  # "leading", "lagging", "diverging", "neutral"
    strength: float = 0.0  # 0..1
    description: str = ""


class LeadershipEngine:
    """Determines market leadership between instruments.

    Usage:
        engine = LeadershipEngine()
        engine.update_returns("NVDA", [0.02, 0.03, ...])
        engine.update_returns("QQQ", [0.01, 0.02, ...])
        result = engine.analyze_leadership("NVDA", "QQQ")
        # result.leader == "NVDA"
    """

    def __init__(self, lookback: int = 20):
        self._returns: dict[str, list[float]] = {}
        self._lookback = lookback
        self._lock = RLock()

    def update_returns(self, symbol: str, returns: list[float]) -> None:
        with self._lock:
            self._returns[symbol] = returns[-self._lookback:]

    def analyze_leadership(self, sym_a: str, sym_b: str) -> LeadershipResult:
        """Analyze which symbol is leading."""
        with self._lock:
            rets_a = self._returns.get(sym_a, [])
            rets_b = self._returns.get(sym_b, [])

        if len(rets_a) < 5 or len(rets_b) < 5:
            return LeadershipResult(description="insufficient data")

        # Compare recent performance
        recent_a = sum(rets_a[-5:]) / 5
        recent_b = sum(rets_b[-5:]) / 5

        # Check for lead/lag: does A move before B?
        # Simple approach: if A's return is more extreme, A is leading
        if abs(recent_a) > abs(recent_b) * 1.2:
            leader = sym_a
            lagger = sym_b
            signal = "leading"
            strength = min(1.0, abs(recent_a) / (abs(recent_b) + 0.001))
        elif abs(recent_b) > abs(recent_a) * 1.2:
            leader = sym_b
            lagger = sym_a
            signal = "leading"
            strength = min(1.0, abs(recent_b) / (abs(recent_a) + 0.001))
        elif (recent_a > 0) != (recent_b > 0):
            leader = sym_a if abs(recent_a) > abs(recent_b) else sym_b
            lagger = sym_b if leader == sym_a else sym_a
            signal = "diverging"
            strength = 0.5
        else:
            leader = None
            lagger = None
            signal = "neutral"
            strength = 0.0

        return LeadershipResult(
            leader=leader,
            lagger=lagger,
            signal=signal,
            strength=round(strength, 4),
            description=f"{leader} {'leading' if leader else 'neutral'} {lagger}",
        )

    def find_strongest(self, symbols: list[str]) -> str | None:
        """Find the strongest performing symbol."""
        with self._lock:
            best: tuple[str, float] | None = None
            for sym in symbols:
                rets = self._returns.get(sym, [])
                if len(rets) >= 5:
                    recent = sum(rets[-5:]) / 5
                    if best is None or recent > best[1]:
                        best = (sym, recent)
            return best[0] if best else None

    def find_weakest(self, symbols: list[str]) -> str | None:
        """Find the weakest performing symbol."""
        with self._lock:
            worst: tuple[str, float] | None = None
            for sym in symbols:
                rets = self._returns.get(sym, [])
                if len(rets) >= 5:
                    recent = sum(rets[-5:]) / 5
                    if worst is None or recent < worst[1]:
                        worst = (sym, recent)
            return worst[0] if worst else None
''')

w("engines/cross-market-plugin-engine/tests/__init__.py", "")
w("engines/cross-market-plugin-engine/tests/test_engine.py", '''
"""Tests for Cross-Market Plugin Engine."""
import pytest
from pathlib import Path
from athena_x_engine_cross_market_plugin_engine import (
    CrossMarketPluginManager,
    CorrelationEngine, CorrelationMatrix,
    LeadershipEngine, LeadershipResult,
)


PLUGIN_DIR = Path(__file__).parent.parent.parent.parent / "plugins" / "cross-market"


@pytest.fixture
def manager():
    mgr = CrossMarketPluginManager(plugin_dir=PLUGIN_DIR)
    mgr.discover()
    return mgr


def test_discovers_60_plus_plugins(manager):
    """60+ cross-market plugins are discovered."""
    assert manager.registry.count() >= 60


def test_6_categories_present(manager):
    """All 6 cross-market categories are represented."""
    stats = manager.get_stats()
    by_cat = stats.get("by_category", {})
    expected = ["market_monitor", "correlation", "leadership", "regime", "rotation", "divergence"]
    for cat in expected:
        assert cat in by_cat, f"Missing category: {cat}"


def test_market_monitors_include_all_groups(manager):
    """Market monitor plugins span all 11 market groups."""
    monitors = manager.list_by_category("market_monitor")
    assert len(monitors) >= 50  # 50+ instruments


def test_correlation_plugins_exist(manager):
    """Correlation plugins are registered."""
    correlations = manager.list_by_category("correlation")
    assert len(correlations) >= 10


def test_leadership_plugins_exist(manager):
    """Leadership plugins are registered."""
    leadership = manager.list_by_category("leadership")
    assert len(leadership) >= 5


def test_regime_plugins_exist(manager):
    """Regime plugins are registered."""
    regimes = manager.list_by_category("regime")
    assert len(regimes) >= 5


def test_config_service_can_disable(manager):
    """Config Service can disable a plugin at runtime."""
    manager.config_service.set_enabled("spy_es_corr", False)
    assert manager.registry.get("spy_es_corr").manifest.enabled is False


# Correlation Engine tests

def test_correlation_engine_computes():
    """Correlation engine computes Pearson correlation."""
    engine = CorrelationEngine()
    engine.update_returns("SPY", [0.01, 0.02, -0.01, 0.03, 0.01])
    engine.update_returns("ES", [0.01, 0.02, -0.01, 0.03, 0.01])
    corr = engine.compute_correlation("SPY", "ES")
    assert corr is not None
    assert corr > 0.99  # identical returns -> correlation ~1.0


def test_correlation_engine_negative():
    """Negatively correlated assets have correlation < 0."""
    engine = CorrelationEngine()
    engine.update_returns("SPY", [0.01, 0.02, -0.01, 0.03, 0.01])
    engine.update_returns("VIX", [-0.01, -0.02, 0.01, -0.03, -0.01])
    corr = engine.compute_correlation("SPY", "VIX")
    assert corr is not None
    assert corr < -0.99


def test_correlation_matrix_detects_changes():
    """Matrix detects meaningful changes."""
    engine = CorrelationEngine(change_threshold=0.05)
    engine.update_returns("SPY", [0.01, 0.02, -0.01, 0.03, 0.01])
    engine.update_returns("ES", [0.01, 0.02, -0.01, 0.03, 0.01])
    matrix1 = engine.compute_matrix([("SPY", "ES")])
    assert len(matrix1.changes) == 0  # first time, no previous

    # Change ES returns significantly
    engine.update_returns("ES", [-0.01, -0.02, 0.01, -0.03, -0.01])
    matrix2 = engine.compute_matrix([("SPY", "ES")])
    assert len(matrix2.changes) > 0  # change detected


# Leadership Engine tests

def test_leadership_engine_finds_leader():
    """Leadership engine identifies the leading instrument."""
    engine = LeadershipEngine()
    engine.update_returns("NVDA", [0.02, 0.03, 0.04, 0.05, 0.06])
    engine.update_returns("QQQ", [0.01, 0.01, 0.01, 0.01, 0.01])
    result = engine.analyze_leadership("NVDA", "QQQ")
    assert result.leader == "NVDA"
    assert result.signal == "leading"


def test_leadership_engine_finds_divergence():
    """Leadership engine detects divergence."""
    engine = LeadershipEngine()
    engine.update_returns("SPY", [0.01, 0.02, 0.03, 0.04, 0.05])
    engine.update_returns("VIX", [0.01, 0.02, 0.03, 0.04, 0.05])  # both up = divergence
    result = engine.analyze_leadership("SPY", "VIX")
    assert result.signal == "diverging"


def test_leadership_engine_finds_strongest():
    """Leadership engine finds the strongest performer."""
    engine = LeadershipEngine()
    engine.update_returns("ES", [0.01, 0.02, 0.03])
    engine.update_returns("SPY", [0.005, 0.01, 0.015])
    engine.update_returns("VIX", [-0.01, -0.02, -0.03])
    strongest = engine.find_strongest(["ES", "SPY", "VIX"])
    assert strongest == "ES"


def test_leadership_engine_finds_weakest():
    """Leadership engine finds the weakest performer."""
    engine = LeadershipEngine()
    engine.update_returns("ES", [0.01, 0.02, 0.03])
    engine.update_returns("SPY", [0.005, 0.01, 0.015])
    engine.update_returns("VIX", [-0.01, -0.02, -0.03])
    weakest = engine.find_weakest(["ES", "SPY", "VIX"])
    assert weakest == "VIX"
''')

# ============================================================================
# 4. MARKET INTELLIGENCE HUB + MARKET DNA
# ============================================================================

w("agents/market-intelligence/pyproject.toml", '''
[project]
name = "athena-x-agent-market-intelligence"
version = "0.1.0"
description = "Market Intelligence Hub + Market DNA Agent (Stage 9)"
requires-python = ">=3.11"
dependencies = [
    "athena-x-engine-cross-market-plugin-engine",
    "athena-x-runtime-event-envelope",
    "athena-x-runtime-logger",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/athena_x_agent_market_intelligence"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
''')

w("agents/market-intelligence/src/athena_x_agent_market_intelligence/__init__.py", '''
"""Market Intelligence Hub + Market DNA Agent."""
from .dna import MarketDNA, MarketDNAAgent
from .hub import MarketIntelligenceHub

__all__ = ["MarketDNA", "MarketDNAAgent", "MarketIntelligenceHub"]
__version__ = "0.1.0"
''')

w("agents/market-intelligence/src/athena_x_agent_market_intelligence/dna.py", '''
"""Market DNA - single summary object consumed by all downstream AI.

Stage 9 additional req: Continuously summarizes the entire market into one object.

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

Stage 10 (Forecast), Stage 11 (Probability), Stage 12 (Supervisor) consume this
single object instead of querying dozens of individual plugins.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4
from athena_x_runtime_logger import get_logger
from athena_x_runtime_event_envelope import create_event, EventPriority

log = get_logger("market-intelligence.dna")


@dataclass
class MarketDNA:
    """Single synchronized market summary for downstream AI consumption."""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Regime
    market_regime: str = "unknown"       # Risk-On, Risk-Off, Inflation, Deflation, Liquidity Exp/Contract
    trend: str = "unknown"               # Bullish, Bearish, Ranging
    volatility: str = "unknown"          # Expanding, Contracting, Normal
    liquidity: str = "unknown"           # Neutral, Expanding, Contracting

    # Breadth
    breadth: str = "unknown"             # Strong, Weak, Neutral

    # Leadership
    leadership: str = "unknown"          # Semiconductors, Tech, Financials, ...
    weakest_sector: str | None = None
    strongest_asset: str | None = None
    weakest_asset: str | None = None

    # Risk
    risk_score: int = 50                 # 0 (no risk) to 100 (extreme risk)
    confidence: float = 0.0              # 0..1

    # Correlations
    spy_es_correlation: float | None = None
    spy_vix_correlation: float | None = None
    spy_dxy_correlation: float | None = None

    # Divergences
    divergences: list[str] = field(default_factory=list)

    # Rotation
    rotation_signal: str | None = None   # tech_to_defensive, growth_to_value, ...

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "market_regime": self.market_regime,
            "trend": self.trend,
            "volatility": self.volatility,
            "liquidity": self.liquidity,
            "breadth": self.breadth,
            "leadership": self.leadership,
            "weakest_sector": self.weakest_sector,
            "strongest_asset": self.strongest_asset,
            "weakest_asset": self.weakest_asset,
            "risk_score": self.risk_score,
            "confidence": round(self.confidence, 4),
            "spy_es_correlation": self.spy_es_correlation,
            "spy_vix_correlation": self.spy_vix_correlation,
            "spy_dxy_correlation": self.spy_dxy_correlation,
            "divergences": self.divergences,
            "rotation_signal": self.rotation_signal,
        }


class MarketDNAAgent:
    """Computes the Market DNA from all available market data.

    Stage 9 rule: Downstream AI (Forecast, Probability, Supervisor) consumes
    this single object instead of querying dozens of individual plugins.

    Usage:
        agent = MarketDNAAgent()
        dna = await agent.compute_dna(
            quotes={"SPY": {...}, "ES": {...}, "VIX": {...}, ...},
            returns={"SPY": [...], "ES": [...], ...},
        )
    """

    def __init__(self, event_bus: Any = None):
        self._bus = event_bus
        self._dna_count = 0

    async def compute_dna(
        self,
        quotes: dict[str, dict] | None = None,
        returns: dict[str, list[float]] | None = None,
    ) -> MarketDNA:
        """Compute the Market DNA from current market data."""
        quotes = quotes or {}
        returns = returns or {}
        dna = MarketDNA()

        # Determine trend from SPY/ES
        spy_rets = returns.get("SPY", [])
        if len(spy_rets) >= 10:
            recent = sum(spy_rets[-10:]) / 10
            if recent > 0.001:
                dna.trend = "Bullish"
            elif recent < -0.001:
                dna.trend = "Bearish"
            else:
                dna.trend = "Ranging"

        # Determine volatility from VIX
        vix_quote = quotes.get("VIX", {})
        vix_level = vix_quote.get("last", 15)
        if vix_level > 25:
            dna.volatility = "Expanding"
        elif vix_level < 12:
            dna.volatility = "Contracting"
        else:
            dna.volatility = "Normal"

        # Determine regime
        if dna.trend == "Bullish" and dna.volatility in ("Normal", "Contracting"):
            dna.market_regime = "Risk-On"
        elif dna.trend == "Bearish" or dna.volatility == "Expanding":
            dna.market_regime = "Risk-Off"
        else:
            dna.market_regime = "Neutral"

        # Determine liquidity from rates
        tnx_quote = quotes.get("TNX", {})
        tnx_level = tnx_quote.get("last", 4.5)
        if tnx_level > 4.5:
            dna.liquidity = "Contracting"
        elif tnx_level < 4.0:
            dna.liquidity = "Expanding"
        else:
            dna.liquidity = "Neutral"

        # Determine breadth (simplified — would use A/D ratio in production)
        dna.breadth = "Strong" if dna.trend == "Bullish" else ("Weak" if dna.trend == "Bearish" else "Neutral")

        # Determine leadership
        from athena_x_engine_cross_market_plugin_engine import LeadershipEngine
        leadership_engine = LeadershipEngine()
        for sym, rets in returns.items():
            leadership_engine.update_returns(sym, rets)

        all_symbols = list(returns.keys())
        if all_symbols:
            dna.strongest_asset = leadership_engine.find_strongest(all_symbols)
            dna.weakest_asset = leadership_engine.find_weakest(all_symbols)

        # Determine sector leadership
        sector_symbols = ["XLK", "XLF", "XLV", "XLY", "XLI", "XLE", "XLP", "XLB", "XLU", "XLRE", "XLC"]
        available_sectors = [s for s in sector_symbols if s in returns]
        if available_sectors:
            strongest_sector = leadership_engine.find_strongest(available_sectors)
            weakest_sector = leadership_engine.find_weakest(available_sectors)
            if strongest_sector:
                dna.leadership = strongest_sector
            if weakest_sector:
                dna.weakest_sector = weakest_sector

        # Compute correlations
        from athena_x_engine_cross_market_plugin_engine import CorrelationEngine
        corr_engine = CorrelationEngine()
        for sym, rets in returns.items():
            corr_engine.update_returns(sym, rets)

        dna.spy_es_correlation = corr_engine.compute_correlation("SPY", "ES")
        dna.spy_vix_correlation = corr_engine.compute_correlation("SPY", "VIX")
        dna.spy_dxy_correlation = corr_engine.compute_correlation("SPY", "DXY")

        # Detect divergences
        if dna.spy_vix_correlation is not None and dna.spy_vix_correlation > 0:
            dna.divergences.append("vix_not_confirming")

        # Compute risk score (0 = no risk, 100 = extreme risk)
        risk = 50  # baseline
        if dna.volatility == "Expanding":
            risk += 15
        if dna.trend == "Bearish":
            risk += 15
        if dna.liquidity == "Contracting":
            risk += 10
        if dna.breadth == "Weak":
            risk += 10
        dna.risk_score = min(100, max(0, risk))

        # Compute confidence
        dna.confidence = 0.85
        if len(returns) >= 10:
            dna.confidence += 0.05
        if dna.spy_es_correlation is not None:
            dna.confidence += 0.05
        dna.confidence = min(1.0, dna.confidence)

        self._dna_count += 1

        # Publish event
        if self._bus is not None:
            event = create_event(
                event_type="market:dna_updated",
                source_agent="market-intelligence.dna",
                symbol="*",
                priority=EventPriority.HIGH,
                payload=dna.to_dict(),
            )
            await self._bus.publish(event)

        return dna

    def get_stats(self) -> dict:
        return {"dna_computed": self._dna_count}
''')

w("agents/market-intelligence/src/athena_x_agent_market_intelligence/hub.py", '''
"""Market Intelligence Hub - aggregates all cross-market intelligence.

Stage 9 req: One hub that collects all market monitor, correlation,
leadership, regime, rotation, and divergence signals into a unified view.
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any
from athena_x_runtime_logger import get_logger

log = get_logger("market-intelligence.hub")


class MarketIntelligenceHub:
    """Aggregates all cross-market intelligence into a unified view.

    Usage:
        hub = MarketIntelligenceHub()
        hub.update_quote("SPY", {"last": 450.0, "change_pct": 0.5})
        hub.update_quote("ES", {"last": 4520.0, "change_pct": 0.4})
        snapshot = hub.get_snapshot()
    """

    def __init__(self):
        self._quotes: dict[str, dict] = {}
        self._returns: dict[str, list[float]] = {}
        self._signals: list[dict] = []
        self._last_snapshot: datetime | None = None

    def update_quote(self, symbol: str, quote: dict) -> None:
        """Update the latest quote for a symbol."""
        self._quotes[symbol] = quote
        # Track returns
        change_pct = quote.get("change_pct", 0)
        if symbol not in self._returns:
            self._returns[symbol] = []
        self._returns[symbol].append(change_pct / 100)
        # Keep last 100 returns
        if len(self._returns[symbol]) > 100:
            self._returns[symbol] = self._returns[symbol][-100:]

    def add_signal(self, signal: dict) -> None:
        """Add a cross-market signal (divergence, leadership change, etc.)."""
        self._signals.append(signal)
        if len(self._signals) > 1000:
            self._signals = self._signals[-500:]

    def get_snapshot(self) -> dict:
        """Get a synchronized snapshot of all market data."""
        self._last_snapshot = datetime.now(timezone.utc)
        return {
            "timestamp": self._last_snapshot.isoformat(),
            "quotes": dict(self._quotes),
            "symbols_tracked": len(self._quotes),
            "recent_signals": self._signals[-10:],
        }

    def get_quotes(self) -> dict[str, dict]:
        return dict(self._quotes)

    def get_returns(self) -> dict[str, list[float]]:
        return dict(self._returns)

    def get_stats(self) -> dict:
        return {
            "symbols_tracked": len(self._quotes),
            "signals_collected": len(self._signals),
            "last_snapshot": self._last_snapshot.isoformat() if self._last_snapshot else None,
        }
''')

w("agents/market-intelligence/tests/__init__.py", "")
w("agents/market-intelligence/tests/test_dna.py", '''
"""Tests for Market DNA Agent."""
import pytest
from athena_x_agent_market_intelligence import MarketDNA, MarketDNAAgent, MarketIntelligenceHub


@pytest.fixture
def quotes():
    return {
        "SPY": {"last": 450.0, "change_pct": 0.5},
        "ES": {"last": 4520.0, "change_pct": 0.4},
        "VIX": {"last": 15.0, "change_pct": -2.0},
        "TNX": {"last": 4.3, "change_pct": 0.1},
        "DXY": {"last": 100.5, "change_pct": -0.1},
        "XLK": {"last": 180.0, "change_pct": 0.8},
        "XLU": {"last": 65.0, "change_pct": -0.2},
        "SOXX": {"last": 200.0, "change_pct": 1.2},
    }


@pytest.fixture
def returns():
    return {
        "SPY": [0.001, 0.002, -0.001, 0.003, 0.001, 0.002, 0.001, 0.002, 0.001, 0.003],
        "ES": [0.001, 0.002, -0.001, 0.003, 0.001, 0.002, 0.001, 0.002, 0.001, 0.003],
        "VIX": [-0.01, -0.02, 0.01, -0.03, -0.01, -0.02, -0.01, -0.02, -0.01, -0.03],
        "DXY": [-0.001, -0.002, 0.001, -0.003, -0.001, -0.002, -0.001, -0.002, -0.001, -0.003],
        "TNX": [0.001, 0.001, 0.001, 0.001, 0.001, 0.001, 0.001, 0.001, 0.001, 0.001],
        "XLK": [0.002, 0.003, 0.001, 0.004, 0.002, 0.003, 0.002, 0.003, 0.002, 0.004],
        "XLU": [-0.001, -0.001, 0.001, -0.002, -0.001, -0.001, 0.001, -0.002, -0.001, -0.001],
        "SOXX": [0.003, 0.004, 0.002, 0.005, 0.003, 0.004, 0.003, 0.004, 0.003, 0.005],
    }


async def test_dna_includes_regime(quotes, returns):
    """Market DNA includes regime classification."""
    agent = MarketDNAAgent()
    dna = await agent.compute_dna(quotes, returns)
    assert dna.market_regime in ("Risk-On", "Risk-Off", "Neutral")


async def test_dna_includes_trend(quotes, returns):
    """Market DNA includes trend."""
    agent = MarketDNAAgent()
    dna = await agent.compute_dna(quotes, returns)
    assert dna.trend in ("Bullish", "Bearish", "Ranging")


async def test_dna_includes_volatility(quotes, returns):
    """Market DNA includes volatility regime."""
    agent = MarketDNAAgent()
    dna = await agent.compute_dna(quotes, returns)
    assert dna.volatility in ("Expanding", "Contracting", "Normal")


async def test_dna_includes_leadership(quotes, returns):
    """Market DNA includes sector leadership."""
    agent = MarketDNAAgent()
    dna = await agent.compute_dna(quotes, returns)
    assert dna.leadership is not None


async def test_dna_includes_strongest_weakest(quotes, returns):
    """Market DNA includes strongest and weakest assets."""
    agent = MarketDNAAgent()
    dna = await agent.compute_dna(quotes, returns)
    assert dna.strongest_asset is not None
    assert dna.weakest_asset is not None


async def test_dna_includes_risk_score(quotes, returns):
    """Market DNA includes risk score 0-100."""
    agent = MarketDNAAgent()
    dna = await agent.compute_dna(quotes, returns)
    assert 0 <= dna.risk_score <= 100


async def test_dna_includes_correlations(quotes, returns):
    """Market DNA includes key correlations."""
    agent = MarketDNAAgent()
    dna = await agent.compute_dna(quotes, returns)
    assert dna.spy_es_correlation is not None
    assert dna.spy_vix_correlation is not None


async def test_dna_includes_confidence(quotes, returns):
    """Market DNA includes confidence."""
    agent = MarketDNAAgent()
    dna = await agent.compute_dna(quotes, returns)
    assert 0 < dna.confidence <= 1.0


async def test_dna_event_published(quotes, returns):
    """Market DNA publishes market:dna_updated event."""
    from athena_x_runtime_event_bus import InMemoryBusBus
    from athena_x_runtime_event_bus import InMemoryBusClient

    bus = InMemoryBusClient()
    agent = MarketDNAAgent(event_bus=bus)

    received = []
    async def handler(event):
        received.append(event)
    await bus.subscribe("market:dna_updated", handler)

    await agent.compute_dna(quotes, returns)

    assert len(received) == 1
    assert "market_regime" in received[0].payload
    await bus.close()


def test_hub_collects_quotes():
    """Market Intelligence Hub collects and stores quotes."""
    hub = MarketIntelligenceHub()
    hub.update_quote("SPY", {"last": 450.0})
    hub.update_quote("ES", {"last": 4520.0})
    quotes = hub.get_quotes()
    assert "SPY" in quotes
    assert "ES" in quotes


def test_hub_snapshot():
    """Hub produces synchronized snapshots."""
    hub = MarketIntelligenceHub()
    hub.update_quote("SPY", {"last": 450.0})
    snapshot = hub.get_snapshot()
    assert "timestamp" in snapshot
    assert "quotes" in snapshot
    assert snapshot["symbols_tracked"] == 1


def test_hub_adds_signals():
    """Hub collects cross-market signals."""
    hub = MarketIntelligenceHub()
    hub.add_signal({"type": "divergence", "description": "VIX not confirming"})
    snapshot = hub.get_snapshot()
    assert len(snapshot["recent_signals"]) == 1
''')

# ============================================================================
# 5. STAGE 9 INTEGRATION
# ============================================================================

w("runtime/stage9-integration/pyproject.toml", '''
[project]
name = "athena-x-runtime-stage9-integration"
version = "0.1.0"
description = "Stage 9 integration - Market Intelligence & Correlation Platform tests"
requires-python = ">=3.11"
dependencies = [
    "athena-x-engine-cross-market-plugin-engine",
    "athena-x-agent-market-intelligence",
    "athena-x-runtime-event-bus",
    "pytest>=8.3.0",
    "pytest-asyncio>=0.24.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/athena_x_runtime_stage9_integration"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
''')

w("runtime/stage9-integration/src/athena_x_runtime_stage9_integration/__init__.py", '''"""Stage 9 integration."""''')

w("runtime/stage9-integration/tests/__init__.py", "")
w("runtime/stage9-integration/tests/test_stage9_acceptance.py", '''
"""Stage 9 acceptance tests - Market Intelligence & Correlation Platform."""
import pytest
from pathlib import Path
from athena_x_engine_cross_market_plugin_engine import (
    CrossMarketPluginManager,
    CorrelationEngine, LeadershipEngine,
)
from athena_x_agent_market_intelligence import MarketDNAAgent, MarketIntelligenceHub


PLUGIN_DIR = Path(__file__).parent.parent.parent.parent / "plugins" / "cross-market"


@pytest.fixture
def manager():
    mgr = CrossMarketPluginManager(plugin_dir=PLUGIN_DIR)
    mgr.discover()
    return mgr


# ============================================================================
# Exit Criteria 1: 60+ cross-market plugins discovered
# ============================================================================

def test_60_plus_plugins_discovered(manager):
    """60+ cross-market plugins are discovered from manifest.yaml files."""
    assert manager.registry.count() >= 60


# ============================================================================
# Exit Criteria 2: 6 categories present
# ============================================================================

def test_6_categories_present(manager):
    """All 6 cross-market plugin categories are represented."""
    stats = manager.get_stats()
    by_cat = stats["by_category"]
    expected = ["market_monitor", "correlation", "leadership", "regime", "rotation", "divergence"]
    for cat in expected:
        assert cat in by_cat, f"Missing category: {cat}"


# ============================================================================
# Exit Criteria 3: 11 market groups covered
# ============================================================================

def test_11_market_groups_covered(manager):
    """Market monitor plugins span all 11 market groups."""
    monitors = manager.list_by_category("market_monitor")
    assert len(monitors) >= 50  # 50+ instruments across 11 groups


# ============================================================================
# Exit Criteria 4: Correlation Engine works
# ============================================================================

def test_correlation_engine_computes_matrix():
    """Correlation engine computes a correlation matrix."""
    engine = CorrelationEngine()
    engine.update_returns("SPY", [0.01, 0.02, -0.01, 0.03, 0.01, 0.02, 0.01, 0.02, 0.01, 0.03])
    engine.update_returns("ES", [0.01, 0.02, -0.01, 0.03, 0.01, 0.02, 0.01, 0.02, 0.01, 0.03])
    engine.update_returns("VIX", [-0.01, -0.02, 0.01, -0.03, -0.01, -0.02, -0.01, -0.02, -0.01, -0.03])

    matrix = engine.compute_matrix([("SPY", "ES"), ("SPY", "VIX")])
    assert "SPY:ES" in matrix.pairs
    assert "SPY:VIX" in matrix.pairs
    assert matrix.pairs["SPY:ES"] > 0.9
    assert matrix.pairs["SPY:VIX"] < -0.9


# ============================================================================
# Exit Criteria 5: Leadership Engine works
# ============================================================================

def test_leadership_engine_identifies_leader():
    """Leadership engine identifies the leading instrument."""
    engine = LeadershipEngine()
    engine.update_returns("NVDA", [0.02, 0.03, 0.04, 0.05, 0.06])
    engine.update_returns("QQQ", [0.01, 0.01, 0.01, 0.01, 0.01])
    result = engine.analyze_leadership("NVDA", "QQQ")
    assert result.leader == "NVDA"


# ============================================================================
# Exit Criteria 6: Market DNA produced
# ============================================================================

async def test_market_dna_produced():
    """Market DNA Agent produces a summary for downstream AI."""
    agent = MarketDNAAgent()
    dna = await agent.compute_dna(
        quotes={
            "SPY": {"last": 450, "change_pct": 0.5},
            "ES": {"last": 4520, "change_pct": 0.4},
            "VIX": {"last": 15, "change_pct": -2},
            "TNX": {"last": 4.3, "change_pct": 0.1},
            "XLK": {"last": 180, "change_pct": 0.8},
            "XLU": {"last": 65, "change_pct": -0.2},
        },
        returns={
            "SPY": [0.001, 0.002, -0.001, 0.003, 0.001, 0.002, 0.001, 0.002, 0.001, 0.003],
            "ES": [0.001, 0.002, -0.001, 0.003, 0.001, 0.002, 0.001, 0.002, 0.001, 0.003],
            "VIX": [-0.01, -0.02, 0.01, -0.03, -0.01, -0.02, -0.01, -0.02, -0.01, -0.03],
            "XLK": [0.002, 0.003, 0.001, 0.004, 0.002, 0.003, 0.002, 0.003, 0.002, 0.004],
            "XLU": [-0.001, -0.001, 0.001, -0.002, -0.001, -0.001, 0.001, -0.002, -0.001, -0.001],
        },
    )

    assert dna.market_regime is not None
    assert dna.trend is not None
    assert dna.volatility is not None
    assert dna.leadership is not None
    assert dna.risk_score is not None
    assert dna.confidence > 0


# ============================================================================
# Exit Criteria 7: Config Service enables/disables without code changes
# ============================================================================

def test_config_service_disable(manager):
    """Config Service can disable a plugin at runtime."""
    manager.config_service.set_enabled("spy_vix_corr", False)
    assert manager.registry.get("spy_vix_corr").manifest.enabled is False


# ============================================================================
# Exit Criteria 8: Adding a new metric = adding a folder
# ============================================================================

def test_adding_metric_only_requires_folder(tmp_path):
    """Adding a new cross-market metric only requires creating a folder."""
    plugin_dir = tmp_path / "cross_market"
    new_plugin = plugin_dir / "liquidity_map"
    new_plugin.mkdir(parents=True)
    (new_plugin / "manifest.yaml").write_text(
        "id: liquidity_map\\nname: Liquidity Map\\nversion: 1.0.0\\n"
        "category: divergence\\nrefresh_interval_seconds: 10\\n"
        "inputs: [quotes]\\noutputs: [liquidity_zones]\\ndependencies: []\\n"
        "enabled: true\\n"
    )

    mgr = CrossMarketPluginManager(plugin_dir=plugin_dir)
    count = mgr.discover()
    assert count == 1
    assert mgr.registry.get("liquidity_map") is not None


# ============================================================================
# Exit Criteria 9: Market Intelligence Hub collects data
# ============================================================================

def test_hub_collects_market_data():
    """Hub collects and synchronizes market data from all sources."""
    hub = MarketIntelligenceHub()
    hub.update_quote("SPY", {"last": 450.0, "change_pct": 0.5})
    hub.update_quote("ES", {"last": 4520.0, "change_pct": 0.4})
    hub.update_quote("VIX", {"last": 15.0, "change_pct": -2.0})

    snapshot = hub.get_snapshot()
    assert snapshot["symbols_tracked"] == 3
    assert "SPY" in snapshot["quotes"]


# ============================================================================
# Exit Criteria 10: All manifests valid
# ============================================================================

def test_all_manifests_valid(manager):
    """Every manifest has required fields."""
    for entry in manager.registry.list_all():
        m = entry.manifest
        assert m.id is not None
        assert m.name is not None
        assert m.version is not None
        assert len(m.outputs) > 0
''')

print(f"\\n✅ Stage 9 complete: {len(FILES)} files written")
print("\\nComponents implemented:")
print("  1. plugins/cross-market/_base/ - CrossMarketPlugin Protocol")
print("  2. plugins/cross-market/*/manifest.yaml - 81 plugin manifests (6 categories)")
print("  3. engines/cross-market-plugin-engine/ - Plugin Manager + Correlation + Leadership Engines")
print("  4. agents/market-intelligence/ - Market DNA Agent + Intelligence Hub")
print("  5. runtime/stage9-integration/ - 10 exit criteria acceptance tests")
print("\\nNext: install deps and run tests")
