"""Configuration for Polygon Options Collector."""
from __future__ import annotations
from pydantic import BaseModel


class PolygonOptionsCollectorConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
