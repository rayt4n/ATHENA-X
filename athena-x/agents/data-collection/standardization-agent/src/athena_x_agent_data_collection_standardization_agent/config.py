"""Configuration for Data Standardization Agent."""
from __future__ import annotations
from pydantic import BaseModel


class StandardizationAgentConfig(BaseModel):
    """Instance configuration. Add fields as needed in STEP 4."""
    enabled: bool = True
