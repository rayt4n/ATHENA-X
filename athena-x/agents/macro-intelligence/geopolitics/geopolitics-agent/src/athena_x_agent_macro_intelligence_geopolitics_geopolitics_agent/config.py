"""Configuration for Geopolitics AI."""
from __future__ import annotations
from pydantic import BaseModel


class GeopoliticsAgentConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
