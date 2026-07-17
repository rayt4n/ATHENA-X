"""Configuration for Accuracy Tracking Agent."""
from __future__ import annotations
from pydantic import BaseModel


class AccuracyTrackingAgentConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
