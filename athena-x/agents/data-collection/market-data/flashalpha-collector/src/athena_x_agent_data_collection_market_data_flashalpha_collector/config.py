"""Configuration for FlashAlpha Collector."""
from __future__ import annotations
from pydantic import BaseModel


class FlashalphaCollectorConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
