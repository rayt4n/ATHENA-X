"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class SupervisorAgentManifest:
    agent_id: str = "supervisor.supervisor-agent"
    name: str = "Supervisor AI"
    division: str = "supervisor"
    team: str = "core"
    layer: str = "supervisor"
    description: str = 'Top-level Supervisor. Every division leader reports here. Detects conflicts, checks stale data, detects failing agents, triggers retries, performs confidence weighting, delegates reports, runs self-le'
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
        # no plugin deps
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = SupervisorAgentManifest()
