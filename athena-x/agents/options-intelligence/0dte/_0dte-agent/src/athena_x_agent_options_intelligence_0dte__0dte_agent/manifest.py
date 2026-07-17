"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class _0DteAgentManifest:
    agent_id: str = "options-intelligence.0dte._0dte-agent"
    name: str = "0DTE AI"
    division: str = "options-intelligence"
    team: str = "0dte"
    layer: str = "5-intelligence"
    description: str = 'Specialized analysis for 0-days-to-expiry options.'
    version: str = "0.1.0"
    subscribes_to: tuple = (
        "market:bar-closed",
    )
    publishes: tuple = (
        "options:iv-updated",
        "options:greeks-computed",
        "options:chain-refreshed",
        "options:gamma-exposure-updated",
        "options:max-pain-updated",
        "options:unusual-activity",
    )
    plugin_dependencies: tuple = (
        # no plugin deps
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = _0DteAgentManifest()
