"""Configuration for Execution AI."""
from __future__ import annotations
from pydantic import BaseModel


class ExecutionAgentConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
