"""Configuration for IV AI."""
from __future__ import annotations
from pydantic import BaseModel


class IvConfig(BaseModel):
    """Instance configuration. Add fields as needed in STEP 4."""
    enabled: bool = True
