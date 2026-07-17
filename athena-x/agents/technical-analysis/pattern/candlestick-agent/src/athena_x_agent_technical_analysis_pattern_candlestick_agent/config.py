"""Configuration for Candlestick AI."""
from __future__ import annotations
from pydantic import BaseModel


class CandlestickAgentConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
