"""Configuration for Ensemble Forecast AI."""
from __future__ import annotations
from pydantic import BaseModel


class EnsembleAgentConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
