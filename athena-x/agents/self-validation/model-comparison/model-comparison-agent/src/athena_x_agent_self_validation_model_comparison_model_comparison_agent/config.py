"""Configuration for Model Comparison Agent."""
from __future__ import annotations
from pydantic import BaseModel


class ModelComparisonAgentConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
