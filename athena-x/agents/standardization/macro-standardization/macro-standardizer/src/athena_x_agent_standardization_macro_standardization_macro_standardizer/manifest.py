"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class MacroStandardizerManifest:
    agent_id: str = "standardization.macro-standardization.macro-standardizer"
    name: str = "Macro Standardizer Agent"
    division: str = "standardization"
    team: str = "macro-standardization"
    layer: str = "3-standardization"
    description: str = 'Converts provider macro data to canonical schema. ONLY writer to macro_db.'
    version: str = "0.1.0"
    subscribes_to: tuple = (
        # source agent
    )
    publishes: tuple = (
        # sink agent
    )
    plugin_dependencies: tuple = (
        # no plugin deps
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = MacroStandardizerManifest()
