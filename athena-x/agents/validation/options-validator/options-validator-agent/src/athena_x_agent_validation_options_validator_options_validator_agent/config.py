"""Configuration for Options Validator Agent."""
from __future__ import annotations
from pydantic import BaseModel


class OptionsValidatorAgentConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
