"""Configuration for 0DTE Team Leader."""
from __future__ import annotations
from pydantic import BaseModel


class TeamLeaderConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
