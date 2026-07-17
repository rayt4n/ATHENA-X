"""Configuration for Smart Money AI."""
from __future__ import annotations
from pydantic import BaseModel


class SmartMoneyAgentConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
