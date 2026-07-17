"""Configuration for Alert Engine Agent."""
from __future__ import annotations
from pydantic import BaseModel


class AlertEngineAgentConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
