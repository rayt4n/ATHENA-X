"""Configuration for Alpha Vantage Collector."""
from __future__ import annotations
from pydantic import BaseModel


class AlphavantageCollectorConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
