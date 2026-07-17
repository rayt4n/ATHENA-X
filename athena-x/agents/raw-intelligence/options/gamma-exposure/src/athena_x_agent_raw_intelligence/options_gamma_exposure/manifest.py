"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class GammaExposureManifest:
    """Manifest for the Gamma Exposure AI."""
    agent_id: str = "raw-intelligence/options.gamma-exposure"
    name: str = "Gamma Exposure AI"
    layer: str = "raw-intelligence/options"
    description: str = "Computes GEX and gamma flip level."
    version: str = "0.1.0"
    subscribes_to: tuple = (
        "options:greeks-computed",
    )
    publishes: tuple = (
        "options:gamma-exposure-updated",
    )
    plugin_dependencies: tuple = (
        "options.gamma-exposure",
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = GammaExposureManifest()
