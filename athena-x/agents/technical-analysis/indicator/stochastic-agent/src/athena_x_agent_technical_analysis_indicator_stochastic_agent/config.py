"""Configuration for Stochastic AI."""
from __future__ import annotations
from pydantic import BaseModel


class StochasticAgentConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
