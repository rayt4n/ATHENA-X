"""Configuration for Finnhub Collector."""
from __future__ import annotations
from pydantic import BaseModel


class FinnhubCollectorConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
