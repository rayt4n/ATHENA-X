"""Configuration for Elliott Wave AI."""
from __future__ import annotations
from pydantic import BaseModel


class ElliottWaveAgentConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
