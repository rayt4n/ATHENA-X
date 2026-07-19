"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class EconomicCalendarAgentManifest:
    agent_id: str = "macro-intelligence.economic-calendar.economic-calendar-agent"
    name: str = "Economic Calendar AI"
    division: str = "macro-intelligence"
    team: str = "economic-calendar"
    layer: str = "5-intelligence"
    description: str = 'CPI, PCE, NFP, GDP, Unemployment releases + surprises.'
    version: str = "0.1.0"
    subscribes_to: tuple = (
        "market:bar-closed",
    )
    publishes: tuple = (
        "macro:indicator-released",
        "macro:yield-curve-updated",
        "macro:fx-rate-updated",
        "macro:commodity-updated",
    )
    plugin_dependencies: tuple = (
        # no plugin deps
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = EconomicCalendarAgentManifest()
