"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ValidationAgentManifest:
    """Manifest for the Data Validation Agent."""
    agent_id: str = "data-collection.validation-agent"
    name: str = "Data Validation Agent"
    layer: str = "data-collection"
    description: str = "Removes duplicates. Detects missing data. Computes data quality scores. Performs cross-provider validation. Rejects low-quality data."
    version: str = "0.1.0"
    subscribes_to: tuple = (
        "market:quote-updated",
        "market:trade-printed",
        "market:bar-closed",
    )
    publishes: tuple = (
        "system:provider-health-updated",
    )
    plugin_dependencies: tuple = (
        # no plugin dependencies
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = ValidationAgentManifest()
