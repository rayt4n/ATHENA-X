"""Configuration for Options Standardizer Agent."""
from __future__ import annotations
from pydantic import BaseModel


class OptionsStandardizerConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
