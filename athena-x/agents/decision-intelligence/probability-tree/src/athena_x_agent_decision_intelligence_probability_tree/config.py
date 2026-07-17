"""Configuration for Probability Tree AI."""
from __future__ import annotations
from pydantic import BaseModel


class ProbabilityTreeConfig(BaseModel):
    """Instance configuration. Add fields as needed in STEP 4."""
    enabled: bool = True
