"""Configuration for FRED Collector."""
from __future__ import annotations
from pydantic import BaseModel


class FredCollectorConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
