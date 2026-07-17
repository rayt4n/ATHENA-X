"""Configuration for MOVE Cross-Market Collector."""
from __future__ import annotations
from pydantic import BaseModel


class MoveCollectorConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
