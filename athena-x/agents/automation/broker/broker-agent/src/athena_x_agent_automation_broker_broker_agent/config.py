"""Configuration for Broker API Adapter."""
from __future__ import annotations
from pydantic import BaseModel


class BrokerAgentConfig(BaseModel):
    """Instance configuration."""
    enabled: bool = True
