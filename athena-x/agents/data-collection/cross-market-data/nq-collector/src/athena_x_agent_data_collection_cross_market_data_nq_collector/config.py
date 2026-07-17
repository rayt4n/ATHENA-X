"""Configuration for NQ Cross-Market Collector."""
from __future__ import annotations
from pydantic import BaseModel


class NqCollectorConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
