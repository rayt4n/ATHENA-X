"""Configuration for WSJ Collector."""
from __future__ import annotations
from pydantic import BaseModel


class WsjCollectorConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
