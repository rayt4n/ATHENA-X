"""Configuration for MACD AI."""
from __future__ import annotations
from pydantic import BaseModel


class MacdAgentConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
