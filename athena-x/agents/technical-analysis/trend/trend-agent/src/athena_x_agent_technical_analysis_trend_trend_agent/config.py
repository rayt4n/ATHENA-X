"""Configuration for Trend AI."""
from __future__ import annotations
from pydantic import BaseModel


class TrendAgentConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
