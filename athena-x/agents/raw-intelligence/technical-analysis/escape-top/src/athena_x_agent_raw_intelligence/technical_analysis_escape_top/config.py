"""Configuration for Escape Top AI."""
from __future__ import annotations
from pydantic import BaseModel


class EscapeTopConfig(BaseModel):
    """Instance configuration. Add fields as needed in STEP 4."""
    enabled: bool = True
