"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class SupervisorAgentManifest:
    """Manifest for the Supervisor AI."""
    agent_id: str = "supervisor.supervisor-agent"
    name: str = "Supervisor AI"
    layer: str = "supervisor"
    description: str = "Every AI agent reports to the Supervisor (Change 3). Detects conflicting signals, checks stale data, detects failing agents, triggers retries, performs confidence weighting, delegates report generation, runs self-learning, and tracks performance statistics."
    version: str = "0.1.0"
    subscribes_to: tuple = (
        "*",
    )
    publishes: tuple = (
        "supervisor:conflict-detected",
        "supervisor:agent-failing",
        "supervisor:retry-requested",
        "supervisor:confidence-adjusted",
    )
    plugin_dependencies: tuple = (
        # no plugin dependencies
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = SupervisorAgentManifest()
