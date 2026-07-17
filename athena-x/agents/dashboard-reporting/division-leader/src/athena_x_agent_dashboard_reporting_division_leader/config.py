"""Configuration for Dashboard & Reporting Division Leader."""
from __future__ import annotations
from pydantic import BaseModel


class DivisionLeaderConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
