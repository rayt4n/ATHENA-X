"""Configuration for SMA AI."""
from __future__ import annotations
from pydantic import BaseModel


class SmaAgentConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
