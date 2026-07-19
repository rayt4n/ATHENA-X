"""Configuration for Fed AI."""
from __future__ import annotations
from pydantic import BaseModel


class FedAgentConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
