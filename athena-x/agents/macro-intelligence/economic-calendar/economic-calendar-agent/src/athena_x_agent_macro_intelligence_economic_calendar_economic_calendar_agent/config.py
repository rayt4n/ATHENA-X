"""Configuration for Economic Calendar AI."""
from __future__ import annotations
from pydantic import BaseModel


class EconomicCalendarAgentConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
