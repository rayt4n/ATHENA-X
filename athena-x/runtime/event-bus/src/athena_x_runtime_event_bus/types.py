"""Bus event types. Mirrors @athena-x/event-schema TypeScript types."""
from __future__ import annotations
from datetime import datetime
from typing import Any, Literal
from uuid import UUID
from pydantic import BaseModel, Field


class BusEvent(BaseModel):
    """Canonical bus event. All 10 metadata fields are required (Change 11)."""
    event_id: UUID = Field(alias="eventId")
    event_type: str = Field(alias="eventType")
    timestamp: datetime
    provider: str
    latency: int = Field(ge=0)
    confidence: float = Field(ge=0.0, le=1.0)
    data_version: str = Field(alias="dataVersion")
    retry_count: int = Field(ge=0, alias="retryCount")
    agent_id: str = Field(alias="agentId")
    processing_time: int = Field(ge=0, alias="processingTime")
    payload: Any

    model_config = {"populate_by_name": True}


class BusClient:
    """Abstract bus client. Implementations: RedisBusClient, NATSBusClient."""

    async def publish(self, event: BusEvent) -> None:
        raise NotImplementedError

    async def subscribe(self, pattern: str, handler) -> None:
        raise NotImplementedError

    async def close(self) -> None:
        raise NotImplementedError
