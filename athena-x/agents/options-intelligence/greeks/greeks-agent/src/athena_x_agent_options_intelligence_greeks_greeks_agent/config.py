"""Configuration for Greeks AI."""
from __future__ import annotations
from pydantic import BaseModel


class GreeksAgentConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
