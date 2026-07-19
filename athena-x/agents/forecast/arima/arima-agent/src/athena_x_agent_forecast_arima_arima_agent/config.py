"""Configuration for ARIMA Forecast AI."""
from __future__ import annotations
from pydantic import BaseModel


class ArimaAgentConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
