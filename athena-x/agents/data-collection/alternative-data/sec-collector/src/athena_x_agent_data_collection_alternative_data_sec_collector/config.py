"""Configuration for SEC Collector."""
from __future__ import annotations
from pydantic import BaseModel


class SecCollectorConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
