"""Configuration for Trend AI."""
from __future__ import annotations
from pydantic import BaseModel


class TrendConfig(BaseModel):
    """Instance configuration. Add fields as needed in STEP 4."""
    enabled: bool = True
