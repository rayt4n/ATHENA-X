"""Configuration for Support/Resistance AI."""
from __future__ import annotations
from pydantic import BaseModel


class SupportResistanceAgentConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
