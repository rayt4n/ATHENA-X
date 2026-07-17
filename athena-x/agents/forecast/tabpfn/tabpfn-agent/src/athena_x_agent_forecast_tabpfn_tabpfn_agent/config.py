"""Configuration for TabPFN Forecast AI."""
from __future__ import annotations
from pydantic import BaseModel


class TabpfnAgentConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
