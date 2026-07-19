"""Configuration for DIA Cross-Market Collector."""
from __future__ import annotations
from pydantic import BaseModel


class DiaCollectorConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
