"""Configuration for Time Validator Agent."""
from __future__ import annotations
from pydantic import BaseModel


class TimeValidatorAgentConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
