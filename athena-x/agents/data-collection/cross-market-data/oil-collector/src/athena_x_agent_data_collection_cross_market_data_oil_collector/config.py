"""Configuration for Oil Cross-Market Collector."""
from __future__ import annotations
from pydantic import BaseModel


class OilCollectorConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
