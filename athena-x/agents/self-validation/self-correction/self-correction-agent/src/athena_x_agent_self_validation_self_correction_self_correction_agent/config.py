"""Configuration for Self-Correction Agent."""
from __future__ import annotations
from pydantic import BaseModel


class SelfCorrectionAgentConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
