"""Configuration for Option Flow AI."""
from __future__ import annotations
from pydantic import BaseModel


class OptionFlowConfig(BaseModel):
    """Instance configuration. Add fields as needed in STEP 4."""
    enabled: bool = True
