"""Configuration for Gamma Flip AI."""
from __future__ import annotations
from pydantic import BaseModel


class GammaFlipAgentConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
