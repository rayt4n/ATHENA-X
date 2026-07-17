"""Configuration for VVIX Cross-Market Collector."""
from __future__ import annotations
from pydantic import BaseModel


class VvixCollectorConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
