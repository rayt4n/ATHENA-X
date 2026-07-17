"""Configuration for Timeframe Sync AI."""
from __future__ import annotations
from pydantic import BaseModel


class TimeframeSyncAgentConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
