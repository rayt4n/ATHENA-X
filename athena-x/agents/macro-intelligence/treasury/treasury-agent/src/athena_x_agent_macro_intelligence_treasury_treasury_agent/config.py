"""Configuration for Treasury AI."""
from __future__ import annotations
from pydantic import BaseModel


class TreasuryAgentConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
