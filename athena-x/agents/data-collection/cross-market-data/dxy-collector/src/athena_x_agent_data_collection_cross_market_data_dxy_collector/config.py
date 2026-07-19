"""Configuration for DXY Cross-Market Collector."""
from __future__ import annotations
from pydantic import BaseModel


class DxyCollectorConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
