"""Configuration for IV Rank AI."""
from __future__ import annotations
from pydantic import BaseModel


class IvRankAgentConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
