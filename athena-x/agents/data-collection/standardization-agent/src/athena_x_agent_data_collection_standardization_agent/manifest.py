"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class StandardizationAgentManifest:
    """Manifest for the Data Standardization Agent."""
    agent_id: str = "data-collection.standardization-agent"
    name: str = "Data Standardization Agent"
    layer: str = "data-collection"
    description: str = "Maps provider-specific schemas to canonical ATHENA-X schema. Normalizes units. Writes validated, standardized data to processed_market_data schema. ONLY writer to processed_market_data."
    version: str = "0.1.0"
    subscribes_to: tuple = (
        "market:quote-updated",
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


MANIFEST = StandardizationAgentManifest()
