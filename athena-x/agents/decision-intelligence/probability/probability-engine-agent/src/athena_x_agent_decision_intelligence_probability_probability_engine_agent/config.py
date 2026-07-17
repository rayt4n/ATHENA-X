"""Configuration for Probability Engine AI."""
from __future__ import annotations
from pydantic import BaseModel


class ProbabilityEngineAgentConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
