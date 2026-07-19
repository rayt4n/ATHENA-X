"""Configuration for FlashAlpha Options Collector."""
from __future__ import annotations
from pydantic import BaseModel


class FlashalphaOptionsCollectorConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
