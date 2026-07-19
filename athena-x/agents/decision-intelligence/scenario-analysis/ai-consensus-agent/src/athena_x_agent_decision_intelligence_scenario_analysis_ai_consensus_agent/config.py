"""Configuration for AI Consensus AI."""
from __future__ import annotations
from pydantic import BaseModel


class AiConsensusAgentConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
