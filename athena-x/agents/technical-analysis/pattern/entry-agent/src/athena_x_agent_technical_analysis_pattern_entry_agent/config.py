"""Configuration for Entry AI."""
from __future__ import annotations
from pydantic import BaseModel


class EntryAgentConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
