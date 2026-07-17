"""Configuration for RSI AI."""
from __future__ import annotations
from pydantic import BaseModel


class RsiConfig(BaseModel):
    """Instance configuration. Add fields as needed in STEP 4."""
    enabled: bool = True
