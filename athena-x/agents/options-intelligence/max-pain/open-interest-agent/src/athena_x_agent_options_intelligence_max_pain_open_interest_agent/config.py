"""Configuration for Open Interest AI."""
from __future__ import annotations
from pydantic import BaseModel


class OpenInterestAgentConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
