"""Configuration for Max Pain AI."""
from __future__ import annotations
from pydantic import BaseModel


class MaxPainAgentConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
