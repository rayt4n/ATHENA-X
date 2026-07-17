"""Configuration for Scenario Analysis AI."""
from __future__ import annotations
from pydantic import BaseModel


class ScenarioAnalysisAgentConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
