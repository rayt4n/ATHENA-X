"""Configuration for XGBoost Forecast AI."""
from __future__ import annotations
from pydantic import BaseModel


class XgboostAgentConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
