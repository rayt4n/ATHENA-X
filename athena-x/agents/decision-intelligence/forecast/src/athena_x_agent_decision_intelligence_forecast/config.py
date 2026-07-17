"""Configuration for AI Forecast Engine."""
from __future__ import annotations
from pydantic import BaseModel


class ForecastConfig(BaseModel):
    """Instance configuration. Add fields as needed in STEP 4."""
    enabled: bool = True
