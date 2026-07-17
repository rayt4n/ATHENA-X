"""Configuration for 0DTE AI."""
from __future__ import annotations
from pydantic import BaseModel


class _0DteConfig(BaseModel):
    """Instance configuration. Add fields as needed in STEP 4."""
    enabled: bool = True
