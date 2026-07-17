"""Configuration for ES Cross-Market Collector."""
from __future__ import annotations
from pydantic import BaseModel


class EsCollectorConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
