"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class MarketRegimeManifest:
    """Manifest for the Market Regime AI."""
    agent_id: str = "decision-intelligence.market-regime"
    name: str = "Market Regime AI"
    layer: str = "decision-intelligence"
    description: str = "Classifies market regime (Change 9): trending/ranging/breakout/mean-reversion/high-vol/low-vol/news-driven/option-driven/dealer-controlled. No indicator is interpreted without regime context."
    version: str = "0.1.0"
    subscribes_to: tuple = (
        "ta:signal-emitted",
        "options:iv-updated",
        "news:impact-classified",
        "macro:indicator-released",
    )
    publishes: tuple = (
        "decision:regime-classified",
    )
    plugin_dependencies: tuple = (
        # no plugin dependencies
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = MarketRegimeManifest()
