"""Configuration for USDJPY Cross-Market Collector."""
from __future__ import annotations
from pydantic import BaseModel


class UsdjpyCollectorConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
