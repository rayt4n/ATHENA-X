"""Configuration for CNBC Collector."""
from __future__ import annotations
from pydantic import BaseModel


class CnbcCollectorConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
