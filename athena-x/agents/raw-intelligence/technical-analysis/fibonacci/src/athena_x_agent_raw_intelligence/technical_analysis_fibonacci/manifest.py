"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class FibonacciManifest:
    """Manifest for the Fibonacci AI."""
    agent_id: str = "raw-intelligence/technical-analysis.fibonacci"
    name: str = "Fibonacci AI"
    layer: str = "raw-intelligence/technical-analysis"
    description: str = "Identifies Fibonacci retracement levels."
    version: str = "0.1.0"
    subscribes_to: tuple = (
        "market:bar-closed",
    )
    publishes: tuple = (
        "ta:level-identified",
        "ta:signal-emitted",
    )
    plugin_dependencies: tuple = (
        "indicators.fibonacci",
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = FibonacciManifest()
