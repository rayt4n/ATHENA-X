"""Configuration for Volatility Surface AI."""
from __future__ import annotations
from pydantic import BaseModel


class VolatilitySurfaceAgentConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
