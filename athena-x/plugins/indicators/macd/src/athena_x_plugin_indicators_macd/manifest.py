"""Plugin manifest — declares capabilities to the plugin-engine."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class MacdManifest:
    id: str = "indicators.macd"
    name: str = "Moving Average Convergence Divergence"
    version: str = "0.1.0"
    type: str = "indicator"
    runtime: str = "python"
    inputs: tuple = ('closes',)
    params: dict = field(default_factory=lambda: {'fast': 12, 'slow': 26, 'signal': 9})
    outputs: tuple = ('macd', 'signal', 'histogram')
    dependencies: tuple = ()


MANIFEST = MacdManifest()
