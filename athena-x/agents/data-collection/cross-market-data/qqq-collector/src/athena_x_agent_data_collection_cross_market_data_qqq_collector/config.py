"""Configuration for QQQ Cross-Market Collector."""
from __future__ import annotations
from pydantic import BaseModel


class QqqCollectorConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
