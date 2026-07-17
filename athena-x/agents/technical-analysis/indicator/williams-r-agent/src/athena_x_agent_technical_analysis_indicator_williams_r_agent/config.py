"""Configuration for Williams %R AI."""
from __future__ import annotations
from pydantic import BaseModel


class WilliamsRAgentConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
