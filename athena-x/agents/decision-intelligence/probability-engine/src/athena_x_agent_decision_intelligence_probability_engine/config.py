"""Configuration for Probability Engine."""
from __future__ import annotations
from pydantic import BaseModel


class ProbabilityEngineConfig(BaseModel):
    """Instance configuration. Add fields as needed in STEP 4."""
    enabled: bool = True
