"""Configuration for Risk AI."""
from __future__ import annotations
from pydantic import BaseModel


class RiskAgentConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
