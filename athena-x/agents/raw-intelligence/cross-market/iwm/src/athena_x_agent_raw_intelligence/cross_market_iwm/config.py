"""Configuration for IWM Cross-Market Agent."""
from __future__ import annotations
from pydantic import BaseModel


class IwmConfig(BaseModel):
    """Instance configuration. Add fields as needed in STEP 4."""
    enabled: bool = True
