"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ValidationAgentManifest:
    """Manifest for the Institutional Validation Agent."""
    agent_id: str = "validator.validation-agent"
    name: str = "Institutional Validation Agent"
    layer: str = "validator"
    description: str = "Institutional Validation Layer (Change 4). Before any report reaches the dashboard: confidence ≥ threshold, evidence ≥ minimum, data freshness within window, source count ≥ minimum, agreement score ≥ threshold. Publishes report-approved or report-rejected."
    version: str = "0.1.0"
    subscribes_to: tuple = (
        "report:generation-completed",
    )
    publishes: tuple = (
        "validator:report-approved",
        "validator:report-rejected",
        "validator:backtest-run",
        "validator:calibration-updated",
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
