"""Configuration for Databento Options Collector."""
from __future__ import annotations
from pydantic import BaseModel


class DatabentoOptionsCollectorConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
