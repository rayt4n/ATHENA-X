"""Configuration for Polymarket Collector."""
from __future__ import annotations
from pydantic import BaseModel


class PolymarketCollectorConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
