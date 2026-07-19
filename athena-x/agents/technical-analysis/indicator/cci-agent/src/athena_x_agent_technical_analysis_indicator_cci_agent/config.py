"""Configuration for CCI AI."""
from __future__ import annotations
from pydantic import BaseModel


class CciAgentConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
