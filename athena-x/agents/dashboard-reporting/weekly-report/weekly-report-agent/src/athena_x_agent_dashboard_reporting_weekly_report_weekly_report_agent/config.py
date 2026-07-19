"""Configuration for Weekly Report Agent."""
from __future__ import annotations
from pydantic import BaseModel


class WeeklyReportAgentConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
