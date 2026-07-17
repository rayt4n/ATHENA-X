"""Configuration for Copper Cross-Market Agent."""
from __future__ import annotations
from pydantic import BaseModel


class CopperConfig(BaseModel):
    """Instance configuration. Add fields as needed in STEP 4."""
    enabled: bool = True
