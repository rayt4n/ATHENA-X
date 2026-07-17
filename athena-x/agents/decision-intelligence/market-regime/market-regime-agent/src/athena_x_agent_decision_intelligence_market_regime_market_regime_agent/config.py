"""Configuration for Market Regime AI."""
from __future__ import annotations
from pydantic import BaseModel


class MarketRegimeAgentConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
