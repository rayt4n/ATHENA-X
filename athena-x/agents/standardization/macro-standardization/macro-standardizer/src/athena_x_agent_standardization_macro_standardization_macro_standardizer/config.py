"""Configuration for Macro Standardizer Agent."""
from __future__ import annotations
from pydantic import BaseModel


class MacroStandardizerConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
