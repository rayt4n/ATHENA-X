"""Configuration for Volume Price AI."""
from __future__ import annotations
from pydantic import BaseModel


class VolumePriceAgentConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
