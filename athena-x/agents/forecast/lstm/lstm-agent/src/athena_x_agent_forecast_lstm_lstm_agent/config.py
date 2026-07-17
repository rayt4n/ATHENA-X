"""Configuration for LSTM Forecast AI."""
from __future__ import annotations
from pydantic import BaseModel


class LstmAgentConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
