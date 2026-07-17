"""Configuration for DXY Cross-Market Agent."""
from __future__ import annotations
from pydantic import BaseModel


class DxyConfig(BaseModel):
    """Instance configuration. Add fields as needed in STEP 4."""
    enabled: bool = True
