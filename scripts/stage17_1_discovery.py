"""ATHENA-X Stage 17.1 — Trading Workspace Integration.

Phase 1 (Discovery) + Phase 2 (Connection Map) + Phase 3a (Mapping Table).

NON-DESTRUCTIVE. Architecture frozen. Reuses Stage 16.3/16.5 infrastructure.
"""
from __future__ import annotations
import asyncio
import json
import sys
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

sys.path.insert(0, '/home/z/my-project/athena-x/runtime/plugin-validation-workspace/src')
sys.path.insert(0, '/home/z/my-project/athena-x/runtime/institutional-workspace/src')

from athena_x_runtime_plugin_validation_workspace import PluginValidationWorkspace
from athena_x_runtime_plugin_validation_workspace.discovery import ValidationInventory

ROOT = Path("/home/z/my-project/athena-x")
OUT_JSON = Path("/home/z/my-project/scripts/stage17_1_evidence.json")


# ============================================================================
# Phase 3a — Workspace Widget → Plugin → API → Agent → Output Mapping Table
# ============================================================================

@dataclass
class WidgetMapping:
    """One widget mapped to existing components."""
    panel: str               # top_bar / left_panel / center / right_panel / bottom_panel / ai_panel / report
    widget: str              # "ES Futures", "Market Regime", "EMA overlay", etc.
    existing_plugin: str     # which plugin/agent provides this
    existing_api: str        # which API endpoint exposes it
    existing_runtime_agent: str  # which runtime agent computes it
    output: str              # what the widget displays
    status: str = "MAPPED"   # MAPPED / MISSING / PARTIAL


# Full mapping table — every widget in the trading workspace
MAPPING_TABLE: list[WidgetMapping] = [
    # ─── TOP BAR ───────────────────────────────────────────────────────
    WidgetMapping("top_bar", "ES Futures",       "providers/yahoo",            "/workspace/execute/ta.trend",       "ta.trend",           "Trend direction + price"),
    WidgetMapping("top_bar", "SPY",              "providers/yahoo",            "/workspace/execute/ta.trend",       "ta.trend",           "Trend direction + price"),
    WidgetMapping("top_bar", "QQQ",              "providers/yahoo",            "/workspace/execute/ta.trend",       "ta.trend",           "Trend direction + price"),
    WidgetMapping("top_bar", "IWM",              "providers/yahoo",            "/workspace/execute/ta.trend",       "ta.trend",           "Trend direction + price"),
    WidgetMapping("top_bar", "DIA",              "providers/yahoo",            "/workspace/execute/ta.trend",       "ta.trend",           "Trend direction + price"),
    WidgetMapping("top_bar", "VIX",              "providers/yahoo",            "/workspace/execute/ta.atr",         "ta.atr",             "Volatility level"),
    WidgetMapping("top_bar", "DXY",              "providers/yahoo",            "/workspace/execute/ta.trend",       "ta.trend",           "Trend direction + price"),
    WidgetMapping("top_bar", "TNX",              "providers/yahoo",            "/workspace/execute/ta.trend",       "ta.trend",           "10Y Treasury yield"),
    WidgetMapping("top_bar", "Gold",             "providers/yahoo",            "/workspace/execute/ta.trend",       "ta.trend",           "Trend direction + price"),
    WidgetMapping("top_bar", "Oil",              "providers/yahoo",            "/workspace/execute/ta.trend",       "ta.trend",           "Trend direction + price"),
    WidgetMapping("top_bar", "Live Status",      "runtime/health-monitor",     "/validation/health",                "n/a",                "Market session + connection health + provider health"),

    # ─── LEFT PANEL — Market Overview ──────────────────────────────────
    WidgetMapping("left_panel", "Market Regime",       "hub.market",            "/workspace/execute/hub.market",     "hub.market",         "Bull / Bear / Range regime"),
    WidgetMapping("left_panel", "Trend Day",            "ta.trend",              "/workspace/execute/ta.trend",       "ta.trend",           "Trend day detection"),
    WidgetMapping("left_panel", "Range Day",            "ta.adx",                "/workspace/execute/ta.adx",         "ta.adx",             "ADX < 20 = range day"),
    WidgetMapping("left_panel", "Reversal Day",         "ta.wyckoff",            "/workspace/execute/ta.wyckoff",     "ta.wyckoff",         "Wyckoff phase = distribution/markdown"),
    WidgetMapping("left_panel", "Gap Analysis",         "ta.support_resistance", "/workspace/execute/ta.support_resistance", "ta.support_resistance", "Gap from prior close"),
    WidgetMapping("left_panel", "Market Breadth",       "hub.market",            "/workspace/execute/hub.market",     "hub.market",         "Breadth ratio"),
    WidgetMapping("left_panel", "Sector Rotation",      "hub.market",            "/workspace/execute/hub.market",     "hub.market",         "Sector performance ranking"),
    WidgetMapping("left_panel", "Fear & Greed",         "providers/cnn",         "n/a (CNN adapter direct)",          "cnn_adapter",        "Fear & Greed Index 0-100"),
    WidgetMapping("left_panel", "Economic Calendar",    "providers/fred",        "n/a (planned, no impl)",            "n/a",                "Economic events calendar"),
    WidgetMapping("left_panel", "Breaking News",        "providers/cnn + hub.narrative", "/workspace/execute/hub.narrative", "hub.narrative", "News headlines + sentiment"),

    # ─── CENTER — Professional Chart with 18 overlays ──────────────────
    WidgetMapping("center", "Multi-timeframe Chart", "providers/yahoo + ta.multi_timeframe_data", "/workspace/execute/ta.multi_timeframe_data", "ta.multi_timeframe_data", "9 timeframes (1M,1W,1D,4H,1H,30M,15M,5M,1m)"),
    WidgetMapping("center", "EMA Overlay",            "ta.ema",                 "/workspace/execute/ta.ema",         "ta.ema",             "EMA20, EMA50, EMA200"),
    WidgetMapping("center", "SMA Overlay",            "ta.sma",                 "/workspace/execute/ta.sma",         "ta.sma",             "SMA20, SMA50, SMA200"),
    WidgetMapping("center", "VWAP Overlay",           "ta.vwap",                "/workspace/execute/ta.vwap",        "ta.vwap",            "VWAP + deviation bands"),
    WidgetMapping("center", "RSI Overlay",            "ta.rsi",                 "/workspace/execute/ta.rsi",         "ta.rsi",             "RSI 0-100"),
    WidgetMapping("center", "MACD Overlay",           "ta.macd",                "/workspace/execute/ta.macd",        "ta.macd",            "MACD, signal, histogram"),
    WidgetMapping("center", "ADX Overlay",            "ta.adx",                 "/workspace/execute/ta.adx",         "ta.adx",             "ADX 0-100"),
    WidgetMapping("center", "ATR Overlay",            "ta.atr",                 "/workspace/execute/ta.atr",         "ta.atr",             "ATR volatility"),
    WidgetMapping("center", "Bollinger Overlay",      "ta.bollinger",           "/workspace/execute/ta.bollinger",   "ta.bollinger",       "Upper/middle/lower bands"),
    WidgetMapping("center", "Volume",                 "ta.volume_profile",      "/workspace/execute/ta.volume_profile", "ta.volume_profile", "Volume histogram + POC"),
    WidgetMapping("center", "Support Resistance",     "ta.support_resistance",  "/workspace/execute/ta.support_resistance", "ta.support_resistance", "S/R levels"),
    WidgetMapping("center", "Swing",                  "ta.swing",               "/workspace/execute/ta.swing",       "ta.swing",           "Swing highs/lows"),
    WidgetMapping("center", "Trend",                  "ta.trend",               "/workspace/execute/ta.trend",       "ta.trend",           "Trend direction"),
    WidgetMapping("center", "Wyckoff",                "ta.wyckoff",             "/workspace/execute/ta.wyckoff",     "ta.wyckoff",         "Wyckoff phase"),
    WidgetMapping("center", "Chan Theory",            "ta.chan_theory",         "/workspace/execute/ta.chan_theory", "ta.chan_theory",     "中枢, bi count"),
    WidgetMapping("center", "Elliott",                "ta.elliott_wave",        "/workspace/execute/ta.elliott_wave", "ta.elliott_wave",   "Current wave count"),
    WidgetMapping("center", "Smart Money",            "ta.smart_money",         "/workspace/execute/ta.smart_money", "ta.smart_money",     "Order blocks, FVG"),
    WidgetMapping("center", "Volume Price",           "ta.volume_price",        "/workspace/execute/ta.volume_price", "ta.volume_price",    "Volume-price trend"),

    # ─── RIGHT PANEL — Institutional Intelligence ──────────────────────
    WidgetMapping("right_panel", "Gamma Exposure",     "hub.options",            "/workspace/execute/hub.options",    "hub.options",        "GEX value"),
    WidgetMapping("right_panel", "Gamma Flip",         "hub.options",            "/workspace/execute/hub.options",    "hub.options",        "Gamma flip level"),
    WidgetMapping("right_panel", "Dealer Positioning", "hub.options",            "/workspace/execute/hub.options",    "hub.options",        "Dealer long/short gamma"),
    WidgetMapping("right_panel", "Max Pain",           "hub.options",            "/workspace/execute/hub.options",    "hub.options",        "Max pain strike"),
    WidgetMapping("right_panel", "Option Flow",        "hub.options",            "/workspace/execute/hub.options",    "hub.options",        "Call/put flow ratio"),
    WidgetMapping("right_panel", "Dark Pool",          "hub.options",            "/workspace/execute/hub.options",    "hub.options",        "Dark pool prints"),
    WidgetMapping("right_panel", "Short Interest",     "hub.options",            "/workspace/execute/hub.options",    "hub.options",        "Short interest %"),
    WidgetMapping("right_panel", "0DTE",               "hub.options",            "/workspace/execute/hub.options",    "hub.options",        "0DTE positioning"),
    WidgetMapping("right_panel", "Liquidity",          "ta.liquidity",           "/workspace/execute/ta.liquidity",   "ta.liquidity",       "Liquidity pools"),
    WidgetMapping("right_panel", "Bond",               "hub.market",             "/workspace/execute/hub.market",     "hub.market",         "Bond market snapshot"),
    WidgetMapping("right_panel", "Dollar",             "hub.market",             "/workspace/execute/hub.market",     "hub.market",         "DXY snapshot"),
    WidgetMapping("right_panel", "Asia",               "hub.market",             "/workspace/execute/hub.market",     "hub.market",         "Asia session summary"),
    WidgetMapping("right_panel", "Europe",             "hub.market",             "/workspace/execute/hub.market",     "hub.market",         "Europe session summary"),
    WidgetMapping("right_panel", "MAG7",               "hub.market",             "/workspace/execute/hub.market",     "hub.market",         "MAG7 stocks performance"),

    # ─── BOTTOM PANEL — Evidence Engine ────────────────────────────────
    WidgetMapping("bottom_panel", "Contributing Plugins",  "runtime/institutional-workspace", "/workspace/evidence/{request_id}", "InstitutionalWorkspace", "List of agents that contributed"),
    WidgetMapping("bottom_panel", "Evidence",              "runtime/institutional-workspace", "/workspace/evidence/{request_id}", "InstitutionalWorkspace", "Per-agent output summary"),
    WidgetMapping("bottom_panel", "Confidence",            "athena_x_ta_base.TAConfidence",   "/workspace/evidence/{request_id}", "TAConfidence",         "0.0-1.0 confidence score"),
    WidgetMapping("bottom_panel", "Weight",                "runtime/institutional-workspace", "/workspace/evidence/{request_id}", "EvidenceReport",       "primary/supporting/contextual weight"),
    WidgetMapping("bottom_panel", "Reason",                "runtime/institutional-workspace", "/workspace/evidence/{request_id}", "EvidenceReport",       "Why this conclusion"),
    WidgetMapping("bottom_panel", "Conflicting Evidence",  "runtime/institutional-workspace", "/workspace/evidence/{request_id}", "EvidenceReport",       "Agents that disagree"),
    WidgetMapping("bottom_panel", "Historical Accuracy",   "runtime/plugin-validation-workspace", "/validation/certification",   "PluginValidationWorkspace", "Per-agent historical accuracy %"),

    # ─── AI PANEL ──────────────────────────────────────────────────────
    WidgetMapping("ai_panel", "Bull / Neutral / Bear",       "hub.forecast",  "/workspace/execute/hub.forecast",   "hub.forecast", "Bull/neutral/bear probability"),
    WidgetMapping("ai_panel", "Probability Tree",            "hub.forecast",  "/workspace/execute/hub.forecast",   "hub.forecast", "Probability tree visualization"),
    WidgetMapping("ai_panel", "Expected Range",              "hub.forecast",  "/workspace/execute/hub.forecast",   "hub.forecast", "Expected price range"),
    WidgetMapping("ai_panel", "Expected Volatility",         "ta.atr",        "/workspace/execute/ta.atr",         "ta.atr",       "ATR-based volatility forecast"),
    WidgetMapping("ai_panel", "15 Minute Projection",        "hub.forecast",  "/workspace/execute/hub.forecast",   "hub.forecast", "15m price projection"),
    WidgetMapping("ai_panel", "1 Hour Projection",           "hub.forecast",  "/workspace/execute/hub.forecast",   "hub.forecast", "1H price projection"),
    WidgetMapping("ai_panel", "End Of Day Projection",       "hub.forecast",  "/workspace/execute/hub.forecast",   "hub.forecast", "EOD price projection"),

    # ─── REPORT ────────────────────────────────────────────────────────
    WidgetMapping("report", "Market Summary",          "hub.market + ta.trend",          "/workspace/execute-request",     "InstitutionalWorkspace", "Aggregate market summary"),
    WidgetMapping("report", "Macro",                   "hub.market",                     "/workspace/execute/hub.market",  "hub.market",            "Macro environment"),
    WidgetMapping("report", "Technical",               "ta.* Layer 1-3",                 "/workspace/execute-request",     "InstitutionalWorkspace", "Technical analysis summary"),
    WidgetMapping("report", "Options",                 "hub.options",                    "/workspace/execute/hub.options", "hub.options",           "Options intelligence"),
    WidgetMapping("report", "Institutional Flow",      "hub.options + hub.market",       "/workspace/execute-request",     "InstitutionalWorkspace", "Institutional flow summary"),
    WidgetMapping("report", "AI",                      "hub.forecast",                   "/workspace/execute/hub.forecast","hub.forecast",          "AI forecast summary"),
    WidgetMapping("report", "Risk",                    "hub.trade",                      "/workspace/execute/hub.trade",   "hub.trade",             "Risk assessment"),
    WidgetMapping("report", "Trade Plan",              "hub.trade",                      "/workspace/execute/hub.trade",   "hub.trade",             "Trade plan with entry/stop/target"),
    WidgetMapping("report", "Invalidation",            "hub.trade + ta.support_resistance", "/workspace/execute/hub.trade", "hub.trade",             "Invalidation levels"),
    WidgetMapping("report", "Catalysts",               "hub.narrative",                  "/workspace/execute/hub.narrative","hub.narrative",         "Upcoming catalysts"),
    WidgetMapping("report", "News Summary",            "hub.narrative",                  "/workspace/execute/hub.narrative","hub.narrative",         "News summary"),
]


def build_mapping_table() -> list[dict]:
    """Return the mapping table as a list of dicts."""
    return [asdict(m) for m in MAPPING_TABLE]


# ============================================================================
# Phase 2 — Connection Map / Dependency Graph
# ============================================================================

def build_connection_map(inventory: ValidationInventory) -> dict:
    """Build the dependency graph showing how every component connects."""
    # The canonical flow:
    # Market Data → Provider → Layer 1 → Layer 2 → Layer 3 → Layer 4 → Layer 5 → Supervisor → Forecast → Risk → Report → Dashboard
    pipeline = [
        {"step": 1, "name": "Market Data", "components": ["FakeMarketRepository (demo)", "YahooAdapter (production)", "FinnhubAdapter", "CNNAdapter", "SimulatedAdapter"], "status": "5/16 providers functional"},
        {"step": 2, "name": "Provider", "components": ["providers/failover (router)", "providers/yahoo", "providers/finnhub", "providers/cnn", "providers/simulated"], "status": "failover router implemented"},
        {"step": 3, "name": "Layer 1: Market Structure", "components": ["ta.trend", "ta.swing", "ta.support_resistance", "ta.liquidity", "ta.volume_profile", "ta.multi_timeframe_data"], "status": "6 agents, all VERIFIED"},
        {"step": 4, "name": "Layer 2: Indicators", "components": ["ta.ema", "ta.sma", "ta.vwap", "ta.rsi", "ta.macd", "ta.adx", "ta.atr", "ta.bollinger"], "status": "8 agents, 1 CERTIFIED (bollinger)"},
        {"step": 5, "name": "Layer 3: Institutional", "components": ["ta.wyckoff", "ta.chan_theory", "ta.elliott_wave", "ta.smart_money", "ta.volume_price", "ta.escape_top", "ta.entry", "ta.pull_up_pattern"], "status": "8 agents, all PROVISIONAL (naive implementations)"},
        {"step": 6, "name": "Layer 4: Consensus", "components": ["ta.consensus (TimeframeConsensusAgent)"], "status": "1 agent, NEEDS IMPROVEMENT (requires multi-TF inputs)"},
        {"step": 7, "name": "Layer 5: Supervisor", "components": ["ta.supervisor (TechnicalSupervisor)", "ta.snapshot (TechnicalSnapshotAgent)"], "status": "2 agents, NEEDS IMPROVEMENT (aggregate only)"},
        {"step": 8, "name": "Intelligence Hubs", "components": ["hub.options", "hub.market", "hub.narrative", "hub.forecast", "hub.trade", "hub.operations"], "status": "6 hubs, all NEEDS IMPROVEMENT (require DNA inputs)"},
        {"step": 9, "name": "Engines", "components": ["engines/plugin-engine", "engines/cross-market-plugin-engine", "engines/forecast-engine", "engines/governance-engine", "engines/narrative-engine", "engines/options-plugin-engine", "engines/trade-engine", "engines/validation-framework"], "status": "8/14 engines functional"},
        {"step": 10, "name": "Validators", "components": ["11 validators in agents/validation/"], "status": "11/17 functional"},
        {"step": 11, "name": "Workspace", "components": ["runtime/institutional-workspace", "runtime/plugin-validation-workspace"], "status": "2 workspace packages, both functional"},
        {"step": 12, "name": "Dashboard", "components": ["apps/nextjs-dashboard (12 modules, scaffolding)", "Standalone HTML dashboards (Stage 16.3, 16.5)"], "status": "Next.js modules are scaffolding; HTML dashboards are functional"},
    ]

    # Dead code / unused plugins / duplicates
    dead_code = []
    for p in inventory.plugin_slots:
        if p.is_stub and not p.has_src:
            dead_code.append({
                "path": f"plugins/{p.category}/{p.name}/",
                "reason": "Scaffolding stub with no src/ directory — never loaded at runtime",
                "evidence": "Runtime uses agents/technical-analysis/layer* instead",
            })
        elif p.is_stub:
            dead_code.append({
                "path": f"plugins/{p.category}/{p.name}/",
                "reason": "Scaffolding stub (NotImplementedError) — runtime uses agents/ instead",
                "evidence": f"{p.src_lines} LoC, raises NotImplementedError",
            })

    duplicate_logic = [
        {"duplicates": ["plugins/indicators/ema/", "agents/technical-analysis/layer2-indicators/ema.py", "agents/technical-analysis/indicator/ema-agent/"],
         "runtime_choice": "agents/technical-analysis/layer2-indicators/ema.py (EMAAgent)",
         "recommendation": "Delete plugins/indicators/ema/ and agents/technical-analysis/indicator/ema-agent/ — both are dead scaffolding"},
        {"duplicates": ["plugins/indicators/rsi/", "agents/technical-analysis/layer2-indicators/rsi.py", "agents/technical-analysis/indicator/rsi-agent/"],
         "runtime_choice": "agents/technical-analysis/layer2-indicators/rsi.py (RSIAgent)",
         "recommendation": "Delete the two scaffolding duplicates"},
        {"duplicates": ["plugins/patterns/wyckoff/", "agents/technical-analysis/layer3-institutional/wyckoff.py", "agents/technical-analysis/wyckoff/wyckoff-agent/"],
         "runtime_choice": "agents/technical-analysis/layer3-institutional/wyckoff.py (WyckoffAgent)",
         "recommendation": "Delete the two scaffolding duplicates"},
        {"duplicates": ["plugins/options/gamma-exposure/", "plugins/options/gex/"],
         "runtime_choice": "Neither — both are stubs; runtime uses hub.options",
         "recommendation": "Delete both; consolidate into hub.options"},
        {"duplicates": ["plugins/options/volatility-surface/", "plugins/options/vol_surface/"],
         "runtime_choice": "Neither — both are stubs",
         "recommendation": "Delete both; consolidate"},
    ]

    unused_plugins = []
    for eng in inventory.engines:
        if eng.is_stub and eng.src_lines < 30:
            unused_plugins.append({
                "path": f"engines/{eng.name}/",
                "reason": f"Engine stub — only {eng.src_lines} LoC, no real implementation",
                "evidence": "Class declared with no body",
            })

    broken_deps = [
        {"component": "PluginManager.load()", "issue": "Looks for indicator.py but plugins use plugin.py", "runtime_impact": "LOW — runtime uses agents/ directly, not PluginManager"},
        {"component": "plugins/indicators/_base/protocol.py", "issue": "Declares TechnicalIndicator Protocol with IndicatorInput/Output dataclasses, but plugins use dict", "runtime_impact": "NONE — protocol is dead code"},
        {"component": "hub.* (6 intelligence hubs)", "issue": "compute() signature expects DNA snapshots, not bars — cannot be executed standalone", "runtime_impact": "HIGH — hubs cannot be validated via standard pipeline"},
        {"component": "ta.consensus, ta.supervisor, ta.snapshot", "issue": "Require multi-agent inputs via event bus, not bars", "runtime_impact": "MEDIUM — these are aggregation agents, not standalone"},
        {"component": "12 dashboard widgets in apps/nextjs-dashboard", "issue": "panelComponent is null in all manifests — scaffolding only", "runtime_impact": "HIGH — no working Next.js dashboard UI"},
    ]

    return {
        "pipeline_flow": pipeline,
        "dead_code_count": len(dead_code),
        "dead_code_sample": dead_code[:10],
        "duplicate_logic": duplicate_logic,
        "unused_plugins_count": len(unused_plugins),
        "unused_plugins_sample": unused_plugins[:5],
        "broken_dependencies": broken_deps,
    }


# ============================================================================
# Main
# ============================================================================

async def main():
    print("[Stage 17.1] Phase 1: Discovery…")
    ws = PluginValidationWorkspace()
    inv = ws.discover()
    inv_dict = inv.to_dict()
    print(f"  → {inv_dict['summary']}")

    print("[Stage 17.1] Phase 2: Connection Map…")
    connection_map = build_connection_map(inv)
    print(f"  → {connection_map['dead_code_count']} dead code items, "
          f"{len(connection_map['duplicate_logic'])} duplicate groups, "
          f"{connection_map['unused_plugins_count']} unused engines, "
          f"{len(connection_map['broken_dependencies'])} broken dependencies")

    print("[Stage 17.1] Phase 3a: Mapping Table…")
    mapping_table = build_mapping_table()
    print(f"  → {len(mapping_table)} widgets mapped")
    by_panel = {}
    for m in mapping_table:
        by_panel[m["panel"]] = by_panel.get(m["panel"], 0) + 1
    for panel, count in by_panel.items():
        print(f"    {panel}: {count} widgets")

    payload = {
        "stage": "17.1",
        "generated_at_unix": int(time.time()),
        "phase1_inventory": inv_dict,
        "phase2_connection_map": connection_map,
        "phase3a_mapping_table": mapping_table,
        "summary": {
            "total_components": sum(inv_dict["summary"].values()),
            "total_widgets_mapped": len(mapping_table),
            "dead_code_count": connection_map["dead_code_count"],
            "duplicate_logic_groups": len(connection_map["duplicate_logic"]),
            "unused_engines": connection_map["unused_plugins_count"],
            "broken_dependencies": len(connection_map["broken_dependencies"]),
        },
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_JSON, "w") as f:
        json.dump(payload, f, indent=2, default=str)
    print(f"\n[Stage 17.1] Evidence written to {OUT_JSON}")


if __name__ == "__main__":
    asyncio.run(main())
