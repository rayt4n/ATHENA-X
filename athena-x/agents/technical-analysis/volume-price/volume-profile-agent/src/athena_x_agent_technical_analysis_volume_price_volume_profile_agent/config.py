"""Configuration for Volume Profile AI."""
from __future__ import annotations
from pydantic import BaseModel


class VolumeProfileAgentConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
