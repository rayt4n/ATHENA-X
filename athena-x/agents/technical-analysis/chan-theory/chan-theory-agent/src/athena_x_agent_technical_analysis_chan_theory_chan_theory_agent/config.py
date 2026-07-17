"""Configuration for Chan Theory AI."""
from __future__ import annotations
from pydantic import BaseModel


class ChanTheoryAgentConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
