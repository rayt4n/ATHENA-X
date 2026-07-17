"""Configuration for Supervisor AI."""
from __future__ import annotations
from pydantic import BaseModel


class SupervisorAgentConfig(BaseModel):
    """Instance configuration. Add fields as needed in STEP 4."""
    enabled: bool = True
