"""Configuration for SPY Intelligence Aggregator."""
from __future__ import annotations
from pydantic import BaseModel


class SpyIntelligenceAggregatorConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
