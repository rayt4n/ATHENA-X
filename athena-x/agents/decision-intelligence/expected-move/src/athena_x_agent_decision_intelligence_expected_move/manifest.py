"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ExpectedMoveManifest:
    """Manifest for the Expected Move AI."""
    agent_id: str = "decision-intelligence.expected-move"
    name: str = "Expected Move AI"
    layer: str = "decision-intelligence"
    description: str = "Computes expected move (Decision Intelligence layer) — combines options-implied + historical + ATR-based."
    version: str = "0.1.0"
    subscribes_to: tuple = (
        "decision:volatility-projected",
        "options:iv-updated",
    )
    publishes: tuple = (
        "decision:expected-move-updated",
    )
    plugin_dependencies: tuple = (
        # no plugin dependencies
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = ExpectedMoveManifest()
