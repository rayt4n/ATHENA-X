"""Configuration for Yahoo Collector."""
from __future__ import annotations
from pydantic import BaseModel


class YahooCollectorConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
