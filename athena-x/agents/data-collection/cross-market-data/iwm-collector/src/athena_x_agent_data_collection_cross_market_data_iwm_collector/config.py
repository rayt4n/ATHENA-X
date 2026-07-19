"""Configuration for IWM Cross-Market Collector."""
from __future__ import annotations
from pydantic import BaseModel


class IwmCollectorConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
