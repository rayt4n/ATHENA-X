"""Configuration for ADX AI."""
from __future__ import annotations
from pydantic import BaseModel


class AdxAgentConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
