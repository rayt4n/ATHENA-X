"""Configuration for SPX Cross-Market Agent."""
from __future__ import annotations
from pydantic import BaseModel


class SpxConfig(BaseModel):
    """Instance configuration. Add fields as needed in STEP 4."""
    enabled: bool = True
