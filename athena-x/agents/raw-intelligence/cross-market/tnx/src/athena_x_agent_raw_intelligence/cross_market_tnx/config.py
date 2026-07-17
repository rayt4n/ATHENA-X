"""Configuration for TNX Cross-Market Agent."""
from __future__ import annotations
from pydantic import BaseModel


class TnxConfig(BaseModel):
    """Instance configuration. Add fields as needed in STEP 4."""
    enabled: bool = True
