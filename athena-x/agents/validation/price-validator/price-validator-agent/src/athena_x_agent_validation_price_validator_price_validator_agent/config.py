"""Configuration for Price Validator Agent."""
from __future__ import annotations
from pydantic import BaseModel


class PriceValidatorAgentConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
