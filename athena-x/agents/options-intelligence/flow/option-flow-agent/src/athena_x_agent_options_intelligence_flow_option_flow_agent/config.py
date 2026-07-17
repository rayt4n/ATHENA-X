"""Configuration for Option Flow AI."""
from __future__ import annotations
from pydantic import BaseModel


class OptionFlowAgentConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
