"""Configuration for IV Crush AI."""
from __future__ import annotations
from pydantic import BaseModel


class IvCrushAgentConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
