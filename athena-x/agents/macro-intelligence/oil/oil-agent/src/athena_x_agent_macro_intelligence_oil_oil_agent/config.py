"""Configuration for Oil AI."""
from __future__ import annotations
from pydantic import BaseModel


class OilAgentConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
