"""Configuration for VWAP AI."""
from __future__ import annotations
from pydantic import BaseModel


class VwapAgentConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
