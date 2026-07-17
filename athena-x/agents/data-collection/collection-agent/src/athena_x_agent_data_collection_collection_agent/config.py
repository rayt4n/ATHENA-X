"""Configuration for Data Collection Agent."""
from __future__ import annotations
from pydantic import BaseModel


class CollectionAgentConfig(BaseModel):
    """Instance configuration. Add fields as needed in STEP 4."""
    enabled: bool = True
