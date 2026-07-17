"""Health metric types (Change 17 — every AI agent exposes 10 metrics)."""
from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class AgentHealth(BaseModel):
    """Change 17 — every AI agent exposes these 10 metrics."""

    model_config = ConfigDict(populate_by_name=True)

    agent_id: str = Field(alias="agentId")
    running: bool
    last_update: datetime | None = Field(default=None, alias="lastUpdate")
    cpu: float = Field(default=0.0, ge=0.0, le=100.0)
    memory: float = Field(default=0.0, ge=0.0, description="MB")
    api_latency: float = Field(default=0.0, ge=0.0, alias="apiLatency", description="ms")
    queue_length: int = Field(default=0, ge=0, alias="queueLength")
    error_count: int = Field(default=0, ge=0, alias="errorCount")
    restart_count: int = Field(default=0, ge=0, alias="restartCount")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    version: str = Field(default="0.1.0")


class ProviderHealth(BaseModel):
    """Change 18 — every provider exposes these 8 metrics."""

    model_config = ConfigDict(populate_by_name=True)

    provider: str
    connection: str = Field(description="connected | disconnected | degraded")
    delay: float = Field(default=0.0, ge=0.0, description="ms")
    missing_bars: int = Field(default=0, ge=0, alias="missingBars")
    missing_ticks: int = Field(default=0, ge=0, alias="missingTicks")
    api_errors: int = Field(default=0, ge=0, alias="apiErrors")
    failover_count: int = Field(default=0, ge=0, alias="failoverCount")
    freshness: float = Field(default=0.0, ge=0.0, description="ms (age of most recent data)")
    reliability_score: float = Field(default=1.0, ge=0.0, le=1.0, alias="reliabilityScore")
