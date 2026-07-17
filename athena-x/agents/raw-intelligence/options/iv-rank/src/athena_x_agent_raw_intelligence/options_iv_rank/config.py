"""Configuration for IV Rank AI."""
from __future__ import annotations
from pydantic import BaseModel


class IvRankConfig(BaseModel):
    """Instance configuration. Add fields as needed in STEP 4."""
    enabled: bool = True
