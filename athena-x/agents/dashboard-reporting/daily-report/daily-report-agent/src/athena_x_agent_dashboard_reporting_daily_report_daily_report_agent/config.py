"""Configuration for Daily Report Agent."""
from __future__ import annotations
from pydantic import BaseModel


class DailyReportAgentConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
