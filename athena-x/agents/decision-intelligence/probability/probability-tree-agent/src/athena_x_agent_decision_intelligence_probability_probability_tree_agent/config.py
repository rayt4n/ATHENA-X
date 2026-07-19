"""Configuration for Probability Tree AI."""
from __future__ import annotations
from pydantic import BaseModel


class ProbabilityTreeAgentConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
