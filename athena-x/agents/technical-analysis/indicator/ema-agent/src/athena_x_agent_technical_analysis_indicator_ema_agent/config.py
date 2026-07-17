"""Configuration for EMA AI."""
from __future__ import annotations
from pydantic import BaseModel


class EmaAgentConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
