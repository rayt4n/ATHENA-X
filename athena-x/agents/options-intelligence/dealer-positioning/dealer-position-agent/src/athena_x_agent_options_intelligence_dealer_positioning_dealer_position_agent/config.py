"""Configuration for Dealer Position AI."""
from __future__ import annotations
from pydantic import BaseModel


class DealerPositionAgentConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
