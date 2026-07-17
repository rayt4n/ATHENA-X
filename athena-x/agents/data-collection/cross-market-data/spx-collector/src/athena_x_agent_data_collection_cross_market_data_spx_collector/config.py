"""Configuration for SPX Cross-Market Collector."""
from __future__ import annotations
from pydantic import BaseModel


class SpxCollectorConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
