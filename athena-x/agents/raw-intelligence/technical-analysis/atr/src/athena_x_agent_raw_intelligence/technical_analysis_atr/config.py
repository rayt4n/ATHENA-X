"""Configuration for ATR AI."""
from __future__ import annotations
from pydantic import BaseModel


class AtrConfig(BaseModel):
    """Instance configuration. Add fields as needed in STEP 4."""
    enabled: bool = True
