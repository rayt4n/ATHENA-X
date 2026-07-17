"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class PriceValidatorAgentManifest:
    agent_id: str = "validation.price-validator.price-validator-agent"
    name: str = "Price Validator Agent"
    division: str = "validation"
    team: str = "price-validator"
    layer: str = "2-validation"
    description: str = 'Cross-source price validation. If Yahoo says 752.44, Polygon 752.46, Finnhub 752.45 → tolerance < 0.02 → Verified. If one says 742 → REJECT.'
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


MANIFEST = PriceValidatorAgentManifest()
