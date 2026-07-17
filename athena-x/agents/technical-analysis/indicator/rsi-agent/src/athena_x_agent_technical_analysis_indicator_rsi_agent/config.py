"""Configuration for RSI AI."""
from __future__ import annotations
from pydantic import BaseModel


class RsiAgentConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
