"""Configuration for Volatility Projection AI."""
from __future__ import annotations
from pydantic import BaseModel


class VolatilityProjectionAgentConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
