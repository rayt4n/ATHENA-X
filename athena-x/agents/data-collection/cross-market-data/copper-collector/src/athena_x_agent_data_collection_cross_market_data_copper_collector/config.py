"""Configuration for Copper Cross-Market Collector."""
from __future__ import annotations
from pydantic import BaseModel


class CopperCollectorConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
