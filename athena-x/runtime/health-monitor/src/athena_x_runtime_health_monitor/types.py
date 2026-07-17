"""Health metrics types."""
from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, Field


class AgentHealth(BaseModel):
    """Change 17 — every AI agent exposes these 10 metrics."""
    agent_id: str = Field(alias="agentId")
    running: bool
    last_update: datetime | None = Field(default=None, alias="lastUpdate")
    cpu: float = Field(ge=0.0, le=100.0)
    memory: float = Field(ge=0.0)  # MB
    api_latency: float = Field(ge=0.0, alias="apiLatency")  # ms
    queue_length: int = Field(ge=0, alias="queueLength")
    error_count: int = Field(ge=0, alias="errorCount")
    restart_count: int = Field(ge=0, alias="restartCount")
    confidence: float = Field(ge=0.0, le=1.0)
    version: str

    model_config = {"populate_by_name": True}


class ProviderHealth(BaseModel):
    """Change 18 — every provider exposes these 8 metrics."""
    provider: str
    connection: str  # connected|disconnected|degraded
    delay: float = Field(ge=0.0)  # ms
    missing_bars: int = Field(ge=0, alias="missingBars")
    missing_ticks: int = Field(ge=0, alias="missingTicks")
    api_errors: int = Field(ge=0, alias="apiErrors")
    failover_count: int = Field(ge=0, alias="failoverCount")
    freshness: float = Field(ge=0.0)  # ms
    reliability_score: float = Field(ge=0.0, le=1.0, alias="reliabilityScore")

    model_config = {"populate_by_name": True}
