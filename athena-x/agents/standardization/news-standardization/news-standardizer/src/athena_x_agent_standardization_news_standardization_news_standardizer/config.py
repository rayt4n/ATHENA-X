"""Configuration for News Standardizer Agent."""
from __future__ import annotations
from pydantic import BaseModel


class NewsStandardizerConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
