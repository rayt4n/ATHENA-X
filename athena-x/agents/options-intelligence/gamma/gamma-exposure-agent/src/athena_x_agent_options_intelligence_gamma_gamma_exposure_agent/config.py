"""Configuration for Gamma Exposure AI."""
from __future__ import annotations
from pydantic import BaseModel


class GammaExposureAgentConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
