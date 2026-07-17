"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class RiskManifest:
    """Manifest for the Risk AI."""
    agent_id: str = "automation.risk"
    name: str = "Risk AI"
    layer: str = "automation"
    description: str = "Pre-trade risk checks (future). Disabled by feature flag. Reserved architecture per Change 16."
    version: str = "0.1.0"
    subscribes_to: tuple = (
        # source agent — no subscriptions
    )
    publishes: tuple = (
        # sink agent — no publications
    )
    plugin_dependencies: tuple = (
        # no plugin dependencies
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = RiskManifest()
