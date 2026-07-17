"""Configuration for Liquidity AI."""
from __future__ import annotations
from pydantic import BaseModel


class LiquidityAgentConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
