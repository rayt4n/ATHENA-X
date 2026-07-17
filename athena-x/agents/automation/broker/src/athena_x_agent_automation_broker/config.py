"""Configuration for Broker API Adapter."""
from __future__ import annotations
from pydantic import BaseModel


class BrokerConfig(BaseModel):
    """Instance configuration. Add fields as needed in STEP 4."""
    enabled: bool = True
