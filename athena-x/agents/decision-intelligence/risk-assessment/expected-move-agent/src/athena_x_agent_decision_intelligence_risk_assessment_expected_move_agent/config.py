"""Configuration for Expected Move AI."""
from __future__ import annotations
from pydantic import BaseModel


class ExpectedMoveAgentConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
