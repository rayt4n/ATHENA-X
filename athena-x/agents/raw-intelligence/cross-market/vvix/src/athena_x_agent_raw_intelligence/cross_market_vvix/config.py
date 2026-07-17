"""Configuration for VVIX Cross-Market Agent."""
from __future__ import annotations
from pydantic import BaseModel


class VvixConfig(BaseModel):
    """Instance configuration. Add fields as needed in STEP 4."""
    enabled: bool = True
