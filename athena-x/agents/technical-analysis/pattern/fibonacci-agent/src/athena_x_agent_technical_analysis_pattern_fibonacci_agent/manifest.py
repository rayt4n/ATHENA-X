"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class FibonacciAgentManifest:
    agent_id: str = "technical-analysis.pattern.fibonacci-agent"
    name: str = "Fibonacci AI"
    division: str = "technical-analysis"
    team: str = "pattern"
    layer: str = "5-intelligence"
    description: str = 'Identifies Fibonacci retracement levels.'
    version: str = "0.1.0"
    subscribes_to: tuple = (
        "market:bar-closed",
    )
    publishes: tuple = (
        "ta:indicator-computed",
        "ta:signal-emitted",
        "ta:level-identified",
    )
    plugin_dependencies: tuple = (
        "indicators.fibonacci",
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = FibonacciAgentManifest()
