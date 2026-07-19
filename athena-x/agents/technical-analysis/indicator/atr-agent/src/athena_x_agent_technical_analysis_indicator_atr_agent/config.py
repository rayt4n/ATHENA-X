"""Configuration for ATR AI."""
from __future__ import annotations
from pydantic import BaseModel


class AtrAgentConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
