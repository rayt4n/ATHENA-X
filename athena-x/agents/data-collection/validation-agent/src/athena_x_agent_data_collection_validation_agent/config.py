"""Configuration for Data Validation Agent."""
from __future__ import annotations
from pydantic import BaseModel


class ValidationAgentConfig(BaseModel):
    """Instance configuration. Add fields as needed in STEP 4."""
    enabled: bool = True
