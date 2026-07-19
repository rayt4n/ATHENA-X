"""Configuration for IV AI."""
from __future__ import annotations
from pydantic import BaseModel


class IvAgentConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
