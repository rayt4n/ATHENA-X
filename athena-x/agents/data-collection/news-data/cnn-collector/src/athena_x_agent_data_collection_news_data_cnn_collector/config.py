"""Configuration for CNN Collector."""
from __future__ import annotations
from pydantic import BaseModel


class CnnCollectorConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
