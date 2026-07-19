"""Configuration for Intraday Report Agent."""
from __future__ import annotations
from pydantic import BaseModel


class IntradayReportAgentConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
