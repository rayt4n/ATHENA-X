"""Configuration for FX AI."""
from __future__ import annotations
from pydantic import BaseModel


class FxAgentConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
