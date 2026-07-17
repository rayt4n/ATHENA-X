"""Configuration for Market Standardizer Agent."""
from __future__ import annotations
from pydantic import BaseModel


class MarketStandardizerConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
