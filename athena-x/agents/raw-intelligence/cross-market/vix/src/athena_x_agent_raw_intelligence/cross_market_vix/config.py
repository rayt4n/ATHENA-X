"""Configuration for VIX Cross-Market Agent."""
from __future__ import annotations
from pydantic import BaseModel


class VixConfig(BaseModel):
    """Instance configuration. Add fields as needed in STEP 4."""
    enabled: bool = True
