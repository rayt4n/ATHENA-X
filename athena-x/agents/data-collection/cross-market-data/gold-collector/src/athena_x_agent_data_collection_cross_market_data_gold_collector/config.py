"""Configuration for Gold Cross-Market Collector."""
from __future__ import annotations
from pydantic import BaseModel


class GoldCollectorConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
