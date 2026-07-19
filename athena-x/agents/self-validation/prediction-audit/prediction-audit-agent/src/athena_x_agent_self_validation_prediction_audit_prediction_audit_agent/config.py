"""Configuration for Prediction Audit Agent."""
from __future__ import annotations
from pydantic import BaseModel


class PredictionAuditAgentConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
