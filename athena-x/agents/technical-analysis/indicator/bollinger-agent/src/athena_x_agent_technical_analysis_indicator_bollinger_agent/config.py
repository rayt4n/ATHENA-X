"""Configuration for Bollinger AI."""
from __future__ import annotations
from pydantic import BaseModel


class BollingerAgentConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
