"""Configuration for Probability of Profit AI."""
from __future__ import annotations
from pydantic import BaseModel


class ProbabilityOfProfitAgentConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
