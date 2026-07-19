"""Configuration for SOXX Cross-Market Collector."""
from __future__ import annotations
from pydantic import BaseModel


class SoxxCollectorConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
