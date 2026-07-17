"""Configuration for Fibonacci AI."""
from __future__ import annotations
from pydantic import BaseModel


class FibonacciAgentConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
