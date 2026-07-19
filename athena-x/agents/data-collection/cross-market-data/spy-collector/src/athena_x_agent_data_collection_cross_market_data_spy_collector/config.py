"""Configuration for SPY Cross-Market Collector."""
from __future__ import annotations
from pydantic import BaseModel


class SpyCollectorConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
