"""Configuration for Execution AI."""
from __future__ import annotations
from pydantic import BaseModel


class ExecutionConfig(BaseModel):
    """Instance configuration. Add fields as needed in STEP 4."""
    enabled: bool = True
