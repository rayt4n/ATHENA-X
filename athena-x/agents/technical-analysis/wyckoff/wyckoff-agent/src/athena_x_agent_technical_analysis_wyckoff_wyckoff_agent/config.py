"""Configuration for Wyckoff AI."""
from __future__ import annotations
from pydantic import BaseModel


class WyckoffAgentConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
