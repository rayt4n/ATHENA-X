"""Configuration for Multi-Timeframe AI."""
from __future__ import annotations
from pydantic import BaseModel


class MultiTimeframeAgentConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
