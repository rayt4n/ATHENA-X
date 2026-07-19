"""Configuration for 0DTE AI."""
from __future__ import annotations
from pydantic import BaseModel


class _0DteAgentConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
