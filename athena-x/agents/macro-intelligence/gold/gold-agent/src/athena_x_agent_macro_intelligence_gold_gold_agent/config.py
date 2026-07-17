"""Configuration for Gold AI."""
from __future__ import annotations
from pydantic import BaseModel


class GoldAgentConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
