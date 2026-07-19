"""Configuration for Reuters Collector."""
from __future__ import annotations
from pydantic import BaseModel


class ReutersCollectorConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
