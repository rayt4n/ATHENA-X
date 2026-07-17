"""Configuration for Polygon Collector."""
from __future__ import annotations
from pydantic import BaseModel


class PolygonCollectorConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
