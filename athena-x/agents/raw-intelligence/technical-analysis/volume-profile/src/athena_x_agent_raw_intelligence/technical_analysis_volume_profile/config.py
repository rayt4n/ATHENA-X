"""Configuration for Volume Profile AI."""
from __future__ import annotations
from pydantic import BaseModel


class VolumeProfileConfig(BaseModel):
    """Instance configuration. Add fields as needed in STEP 4."""
    enabled: bool = True
