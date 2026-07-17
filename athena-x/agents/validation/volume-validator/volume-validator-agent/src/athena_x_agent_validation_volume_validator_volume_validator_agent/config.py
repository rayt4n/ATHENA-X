"""Configuration for Volume Validator Agent."""
from __future__ import annotations
from pydantic import BaseModel


class VolumeValidatorAgentConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
