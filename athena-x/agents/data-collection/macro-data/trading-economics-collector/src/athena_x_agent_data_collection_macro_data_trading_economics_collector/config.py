"""Configuration for Trading Economics Collector."""
from __future__ import annotations
from pydantic import BaseModel


class TradingEconomicsCollectorConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
