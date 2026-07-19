"""Configuration for Asia Cross-Market Collector."""
from __future__ import annotations
from pydantic import BaseModel


class AsiaCollectorConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
