"""Configuration for Asia Cross-Market Agent."""
from __future__ import annotations
from pydantic import BaseModel


class AsiaConfig(BaseModel):
    """Instance configuration. Add fields as needed in STEP 4."""
    enabled: bool = True
