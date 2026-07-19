"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class XgboostAgentManifest:
    agent_id: str = "forecast.xgboost.xgboost-agent"
    name: str = "XGBoost Forecast AI"
    division: str = "forecast"
    team: str = "xgboost"
    layer: str = "5-intelligence"
    description: str = 'XGBoost + CatBoost + LightGBM-large. Python GPU.'
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


MANIFEST = XgboostAgentManifest()
