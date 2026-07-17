"""Configuration for Transformer Forecast AI."""
from __future__ import annotations
from pydantic import BaseModel


class TransformerAgentConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
