"""Configuration for Open Interest AI."""
from __future__ import annotations
from pydantic import BaseModel


class OpenInterestConfig(BaseModel):
    """Instance configuration. Add fields as needed in STEP 4."""
    enabled: bool = True
