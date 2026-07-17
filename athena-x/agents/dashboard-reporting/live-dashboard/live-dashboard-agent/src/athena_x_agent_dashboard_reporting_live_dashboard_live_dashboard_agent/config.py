"""Configuration for Live Dashboard Agent."""
from __future__ import annotations
from pydantic import BaseModel


class LiveDashboardAgentConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
