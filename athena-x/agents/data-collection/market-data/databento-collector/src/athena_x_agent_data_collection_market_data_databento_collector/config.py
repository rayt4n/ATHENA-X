"""Configuration for Databento Collector."""
from __future__ import annotations
from pydantic import BaseModel


class DatabentoCollectorConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
