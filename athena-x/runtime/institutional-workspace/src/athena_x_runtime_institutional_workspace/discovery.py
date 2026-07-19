"""Runtime Discovery — auto-discovers every verified TA agent and intelligence hub.

Walks the agents/technical-analysis/layer* packages and agents/*-intelligence/
hub packages, imports each, and records:
  - agent_id (e.g., "ta.ema", "options-intelligence")
  - class_name (e.g., "EMAAgent")
  - layer (1..5 or "hub")
  - file_path
  - inputs (declared via BarCache or event subscriptions)
  - outputs (declared via TAOutput.indicator field)
  - dependencies (Layer 3 depends on Layer 1+2, etc.)

Does NOT instantiate agents. Discovery is metadata-only.
"""
from __future__ import annotations
import importlib
import inspect
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from athena_x_runtime_logger import get_logger

log = get_logger("institutional-workspace.discovery")


@dataclass(frozen=True)
class DiscoveredAgent:
    """Metadata for one discovered runtime agent."""
    agent_id: str               # e.g., "ta.ema", "ta.wyckoff", "options-intelligence"
    class_name: str             # e.g., "EMAAgent"
    module_path: str            # e.g., "athena_x_ta_layer2_indicators.ema"
    file_path: str              # absolute filesystem path
    layer: int | str            # 1..5 for TA layers, "hub" for intelligence hubs
    category: str               # "market_structure" / "indicator" / "institutional" / "consensus" / "supervisor" / "snapshot" / "options" / "market" / "narrative" / "forecast" / "trade" / "operations"
    description: str = ""
    inputs: tuple[str, ...] = ()
    outputs: tuple[str, ...] = ()
    dependencies: tuple[str, ...] = ()
    compute_signature: str = ""


# Mapping of (package_name, layer, category) for TA Layer agents
TA_LAYER_PACKAGES = [
    ("athena_x_ta_layer1_market_structure", 1, "market_structure"),
    ("athena_x_ta_layer2_indicators",        2, "indicator"),
    ("athena_x_ta_layer3_institutional",     3, "institutional"),
    ("athena_x_ta_layer4_consensus",         4, "consensus"),
    ("athena_x_ta_layer5_supervisor",        5, "supervisor"),
    ("athena_x_ta_snapshot",                 5, "snapshot"),
]

# Mapping of (package_name, category) for intelligence hub agents
HUB_PACKAGES = [
    ("athena_x_agent_options_intelligence",    "options"),
    ("athena_x_agent_market_intelligence",     "market"),
    ("athena_x_agent_narrative_intelligence",  "narrative"),
    ("athena_x_agent_forecast_intelligence",   "forecast"),
    ("athena_x_agent_trade_intelligence",      "trade"),
    ("athena_x_agent_operations_governance",   "operations"),
]


# Known agent name → (inputs, outputs) for TA Layer agents.
# This is derived from reading the source code; encoded here for the dashboard.
TA_AGENT_IO_MAP = {
    # Layer 1: market structure
    "trend":               (["bars(50)"], ["Trend: bullish|bearish|ranging"]),
    "swing":               (["bars(100)"], ["SwingHL: swing_highs, swing_lows"]),
    "support_resistance":  (["bars(100)"], ["SR: resistance, support"]),
    "liquidity":           (["bars(50)"],  ["Liquidity: liquidity_pools, avg_volume"]),
    "volume_profile":      (["bars(100)"], ["VolumeProfile: POC, value_area"]),
    "multi_timeframe_data":(["bars(9 TFs)"], ["MTF: per-TF bars"]),
    # Layer 2: indicators
    "ema":        (["bars(period*3)"], ["EMA{period}: float"]),
    "sma":        (["bars(period)"],   ["SMA{period}: float"]),
    "vwap":       (["bars(1d)"],       ["VWAP: float, deviation_bands"]),
    "rsi":        (["bars(period)"],   ["RSI{period}: float 0..100"]),
    "macd":       (["bars(26+9)"],     ["MACD: macd, signal, histogram"]),
    "adx":        (["bars(period*2)"], ["ADX{period}: float 0..100"]),
    "atr":        (["bars(period+1)"], ["ATR{period}: float"]),
    "bollinger":  (["bars(period)"],   ["Bollinger: upper, middle, lower, percent_b"]),
    # Layer 3: institutional
    "wyckoff":         (["bars(100)"], ["Wyckoff: phase (accumulation|markup|distribution)"]),
    "chan_theory":     (["bars(100)"], ["Chan: bi_count, zhongshu_detected"]),
    "elliott_wave":    (["bars(100)"], ["Elliott: current_wave (1..5|corrective)"]),
    "smart_money":     (["bars(100)"], ["SmartMoney: order_blocks, fvg_detected"]),
    "volume_price":    (["bars(100)"], ["VolumePrice: volume_trend, price_trend"]),
    "escape_top":      (["bars(100)"], ["EscapeTop: escape_detected, consolidation_range"]),
    "entry":           (["bars(100)"], ["Entry: entry_signal (long|short|wait)"]),
    "pull_up_pattern": (["bars(100)"], ["PullUp: pull_up_detected, strength"]),
    # Layer 4
    "consensus":  (["bars(9 TFs)"], ["Consensus: alignment, long_term, intraday"]),
    # Layer 5
    "supervisor": (["agent health dicts"], ["SystemHealth: readiness_score, offline_agents"]),
    "snapshot":   (["all layer outputs"], ["TechnicalSnapshot: aggregate DNA"]),
}

# Layer dependencies (who consumes whose output)
LAYER_DEPENDENCIES = {
    1: (),       # Layer 1 reads bars only
    2: (1,),     # Layer 2 indicators may consume Layer 1 context (via event bus)
    3: (1, 2),   # Layer 3 explicitly consumes Layer 1+2 outputs
    4: (1, 2, 3),
    5: (1, 2, 3, 4),
}


def _discover_ta_layer_agents() -> list[DiscoveredAgent]:
    """Discover every TA agent in athena_x_ta_layer* packages."""
    discovered: list[DiscoveredAgent] = []
    for pkg_name, layer, category in TA_LAYER_PACKAGES:
        try:
            pkg = importlib.import_module(pkg_name)
        except ImportError as e:
            log.warning("ta_layer_import_failed", package=pkg_name, error=str(e))
            continue

        # The package __init__.py exports the agent classes
        exported = [name for name in dir(pkg)
                    if name.endswith("Agent") and not name.startswith("_") and name != "BaseTAAgent"]
        for cls_name in exported:
            cls = getattr(pkg, cls_name)
            if not isinstance(cls, type):
                continue
            try:
                module = inspect.getmodule(cls)
                module_path = module.__name__ if module else ""
                file_path = inspect.getfile(cls)
            except Exception:
                module_path = pkg_name
                file_path = ""

            # Derive agent_id from class name (EMAAgent → "ema")
            agent_name = cls_name.replace("Agent", "").lower()
            # Handle special cases
            special = {
                "trenddetection": "trend",
                "swinghighlow": "swing",
                "supportresistance": "support_resistance",
                "volumeprofile": "volume_profile",
                "multitimeframedata": "multi_timeframe_data",
                "timeframeconsensus": "consensus",
                "technicalsupervisor": "supervisor",
                "technicalsnapshot": "snapshot",
                "elliottwave": "elliott_wave",
                "chantheory": "chan_theory",
                "smartmoney": "smart_money",
                "volumeprice": "volume_price",
                "escapetop": "escape_top",
                "pulluppattern": "pull_up_pattern",
            }
            agent_name = special.get(agent_name, agent_name)
            agent_id = f"ta.{agent_name}"

            io = TA_AGENT_IO_MAP.get(agent_name, (["bars"], ["TAOutput"]))
            deps = tuple(f"ta.{d}" for d in [] )  # populated via LAYER_DEPENDENCIES below

            discovered.append(DiscoveredAgent(
                agent_id=agent_id,
                class_name=cls_name,
                module_path=module_path,
                file_path=file_path,
                layer=layer,
                category=category,
                description=cls.__doc__ or "",
                inputs=tuple(io[0]),
                outputs=tuple(io[1]),
                dependencies=tuple(f"layer{d}" for d in LAYER_DEPENDENCIES.get(layer, ())),
                compute_signature="async compute(symbol: str, timeframe: Timeframe, repo) -> TAOutput",
            ))
    return discovered


def _discover_hub_agents() -> list[DiscoveredAgent]:
    """Discover intelligence hub agents."""
    discovered: list[DiscoveredAgent] = []
    for pkg_name, category in HUB_PACKAGES:
        try:
            pkg = importlib.import_module(pkg_name)
        except ImportError as e:
            log.warning("hub_import_failed", package=pkg_name, error=str(e))
            continue

        # Hub packages export their primary agent class from __init__.py or from a submodule
        # Find classes ending in "Agent" or "Hub"
        candidates = []
        for name in dir(pkg):
            if name.startswith("_"):
                continue
            obj = getattr(pkg, name)
            if isinstance(obj, type) and ("Agent" in name or "Hub" in name):
                candidates.append((name, obj))

        if not candidates:
            # Try common submodule names
            for sub in ("agent", "hub", "narrative_agent", "forecast_agent"):
                try:
                    submod = importlib.import_module(f"{pkg_name}.{sub}")
                    for name in dir(submod):
                        if name.startswith("_"):
                            continue
                        obj = getattr(submod, name)
                        if isinstance(obj, type) and ("Agent" in name or "Hub" in name):
                            candidates.append((name, obj))
                except ImportError:
                    continue

        for cls_name, cls in candidates:
            try:
                module = inspect.getmodule(cls)
                module_path = module.__name__ if module else pkg_name
                file_path = inspect.getfile(cls)
            except Exception:
                module_path = pkg_name
                file_path = ""

            # Use category as the agent_id
            agent_id = f"hub.{category}"
            discovered.append(DiscoveredAgent(
                agent_id=agent_id,
                class_name=cls_name,
                module_path=module_path,
                file_path=file_path,
                layer="hub",
                category=category,
                description=cls.__doc__ or "",
                inputs=("DNA snapshots", "events"),
                outputs=(f"{category} intelligence snapshot",),
                dependencies=("layer1", "layer2", "layer3", "layer4", "layer5"),
                compute_signature="async run() -> IntelligenceSnapshot",
            ))
            break  # one hub per package
    return discovered


class RuntimeDiscovery:
    """Discovers all runtime agents without instantiating them."""

    def discover_all(self) -> list[DiscoveredAgent]:
        """Return every discovered agent across TA layers + intelligence hubs."""
        ta = _discover_ta_layer_agents()
        hubs = _discover_hub_agents()
        all_agents = ta + hubs
        log.info("agents_discovered",
                 total=len(all_agents),
                 ta_layer=len(ta),
                 hub=len(hubs))
        return all_agents

    def discover_by_layer(self, layer: int | str) -> list[DiscoveredAgent]:
        return [a for a in self.discover_all() if a.layer == layer]

    def discover_by_category(self, category: str) -> list[DiscoveredAgent]:
        return [a for a in self.discover_all() if a.category == category]

    def get_summary(self) -> dict:
        agents = self.discover_all()
        by_layer: dict[str, int] = {}
        by_category: dict[str, int] = {}
        for a in agents:
            key = str(a.layer)
            by_layer[key] = by_layer.get(key, 0) + 1
            by_category[a.category] = by_category.get(a.category, 0) + 1
        return {
            "total_agents": len(agents),
            "by_layer": by_layer,
            "by_category": by_category,
        }
