"""Configuration for Europe Cross-Market Collector."""
from __future__ import annotations
from pydantic import BaseModel


class EuropeCollectorConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
