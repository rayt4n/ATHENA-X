"""Configuration for TNX Cross-Market Collector."""
from __future__ import annotations
from pydantic import BaseModel


class TnxCollectorConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
