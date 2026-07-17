"""Configuration for Bond Market AI."""
from __future__ import annotations
from pydantic import BaseModel


class BondMarketAgentConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
