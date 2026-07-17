"""Configuration for News Validator Agent."""
from __future__ import annotations
from pydantic import BaseModel


class NewsValidatorAgentConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
