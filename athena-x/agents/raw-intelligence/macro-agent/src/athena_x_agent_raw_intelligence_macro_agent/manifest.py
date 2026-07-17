"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class MacroAgentManifest:
    """Manifest for the Macro Agent."""
    agent_id: str = "raw-intelligence.macro-agent"
    name: str = "Macro Agent"
    layer: str = "raw-intelligence"
    description: str = "Ingests macro indicators from FRED (US), ECB (EU), PBoC (CN), BoJ (JP), ONS (UK)."
    version: str = "0.1.0"
    subscribes_to: tuple = (
        # source agent — no subscriptions
    )
    publishes: tuple = (
        "macro:indicator-released",
        "macro:yield-curve-updated",
        "macro:fx-rate-updated",
        "macro:commodity-updated",
    )
    plugin_dependencies: tuple = (
        # no plugin dependencies
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = MacroAgentManifest()
