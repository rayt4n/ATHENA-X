"""Configuration for Supervisor AI."""
from __future__ import annotations
from pydantic import BaseModel


class SupervisorAgentConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
