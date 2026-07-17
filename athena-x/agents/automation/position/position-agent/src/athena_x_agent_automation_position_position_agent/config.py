"""Configuration for Position AI."""
from __future__ import annotations
from pydantic import BaseModel


class PositionAgentConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
