"""Configuration for Ichimoku AI."""
from __future__ import annotations
from pydantic import BaseModel


class IchimokuAgentConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
