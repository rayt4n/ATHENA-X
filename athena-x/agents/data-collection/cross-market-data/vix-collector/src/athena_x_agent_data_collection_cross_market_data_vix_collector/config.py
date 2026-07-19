"""Configuration for VIX Cross-Market Collector."""
from __future__ import annotations
from pydantic import BaseModel


class VixCollectorConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
