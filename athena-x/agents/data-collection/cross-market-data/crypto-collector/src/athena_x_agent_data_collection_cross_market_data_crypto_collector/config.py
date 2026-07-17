"""Configuration for Crypto Cross-Market Collector."""
from __future__ import annotations
from pydantic import BaseModel


class CryptoCollectorConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
