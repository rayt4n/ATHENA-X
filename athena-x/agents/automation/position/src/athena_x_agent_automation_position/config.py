"""Configuration for Position AI."""
from __future__ import annotations
from pydantic import BaseModel


class PositionConfig(BaseModel):
    """Instance configuration. Add fields as needed in STEP 4."""
    enabled: bool = True
