"""Configuration for OBV AI."""
from __future__ import annotations
from pydantic import BaseModel


class ObvAgentConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
