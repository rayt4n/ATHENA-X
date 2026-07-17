"""Configuration for Pull-Up Pattern AI."""
from __future__ import annotations
from pydantic import BaseModel


class PullUpPatternAgentConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
