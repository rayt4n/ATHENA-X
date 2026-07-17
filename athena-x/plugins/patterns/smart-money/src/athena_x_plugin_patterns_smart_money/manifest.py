"""Plugin manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class SmartMoneyManifest:
    id: str = "patterns.smart-money"
    name: str = "Smart Money Concept Detector"
    version: str = "0.1.0"
    type: str = "pattern"
    runtime: str = "python"
    inputs: tuple = ('bars',)
    params: dict = field(default_factory=dict)
    outputs: tuple = ('order_blocks', 'fair_value_gaps', 'liquidity')
    dependencies: tuple = ()


MANIFEST = SmartMoneyManifest()
