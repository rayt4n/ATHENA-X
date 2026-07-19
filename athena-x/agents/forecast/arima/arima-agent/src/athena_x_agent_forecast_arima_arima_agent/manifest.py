"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ArimaAgentManifest:
    agent_id: str = "forecast.arima.arima-agent"
    name: str = "ARIMA Forecast AI"
    division: str = "forecast"
    team: str = "arima"
    layer: str = "5-intelligence"
    description: str = 'Statistical ARIMA model. Lightweight, runs on CPU.'
    version: str = "0.1.0"
    subscribes_to: tuple = (
        "market:bar-closed",
    )
    publishes: tuple = (
        "forecast:trajectory-computed",
        "forecast:catalyst-detected",
    )
    plugin_dependencies: tuple = (
        # no plugin deps
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = ArimaAgentManifest()
