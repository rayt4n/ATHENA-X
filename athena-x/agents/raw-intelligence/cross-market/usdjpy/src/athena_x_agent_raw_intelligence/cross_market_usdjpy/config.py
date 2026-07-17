"""Configuration for USDJPY Cross-Market Agent."""
from __future__ import annotations
from pydantic import BaseModel


class UsdjpyConfig(BaseModel):
    """Instance configuration. Add fields as needed in STEP 4."""
    enabled: bool = True
