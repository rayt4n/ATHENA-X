"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class CandlestickManifest:
    """Manifest for the Candlestick AI."""
    agent_id: str = "raw-intelligence/technical-analysis.candlestick"
    name: str = "Candlestick AI"
    layer: str = "raw-intelligence/technical-analysis"
    description: str = "Recognizes candlestick patterns (doji, hammer, engulfing, etc.)."
    version: str = "0.1.0"
    subscribes_to: tuple = (
        "market:bar-closed",
    )
    publishes: tuple = (
        "ta:signal-emitted",
    )
    plugin_dependencies: tuple = (
        "patterns.candlestick",
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = CandlestickManifest()
