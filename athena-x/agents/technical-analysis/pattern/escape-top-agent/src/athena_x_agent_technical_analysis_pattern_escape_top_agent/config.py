"""Configuration for Escape Top AI."""
from __future__ import annotations
from pydantic import BaseModel


class EscapeTopAgentConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
