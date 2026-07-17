"""
Canonical bus event types.

Every event MUST contain 10 mandatory metadata fields (STEP 3.5 Change 11):
  1. eventId         (UUID)
  2. eventType       (string, e.g., "market:quote-updated")
  3. timestamp       (ISO 8601 UTC)
  4. provider        (string — source provider/agent)
  5. latency         (ms — source to bus publish)
  6. confidence      (0..1)
  7. dataVersion     (semver of payload schema)
  8. retryCount      (0 on first publish)
  9. agentId         (emitting agent ID)
 10. processingTime  (ms the agent spent producing this)

Events missing any field are REJECTED at the bus boundary.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Literal
from uuid import UUID, uuid4
from pydantic import BaseModel, ConfigDict, Field, field_validator


EventHandler = Callable[["BusEvent"], Awaitable[None]]


class BusEventMeta(BaseModel):
    """The 10 mandatory metadata fields. Reused across all event types."""

    model_config = ConfigDict(populate_by_name=True, frozen=True)

    event_id: UUID = Field(alias="eventId")
    event_type: str = Field(alias="eventType", min_length=1)
    timestamp: datetime = Field()
    provider: str = Field(min_length=1)
    latency: int = Field(ge=0, description="ms from source to publish")
    confidence: float = Field(ge=0.0, le=1.0)
    data_version: str = Field(alias="dataVersion", pattern=r"^\d+\.\d+\.\d+$")
    retry_count: int = Field(alias="retryCount", ge=0)
    agent_id: str = Field(alias="agentId", min_length=1)
    processing_time: int = Field(alias="processingTime", ge=0,
        description="ms the agent spent producing this event")

    @field_validator("timestamp")
    @classmethod
    def must_be_utc(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("timestamp must be timezone-aware (UTC)")
        return v


class BusEvent(BusEventMeta):
    """A complete bus event: metadata + payload."""

    model_config = ConfigDict(populate_by_name=True, frozen=False)

    payload: Any = Field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        event_type: str,
        provider: str,
        agent_id: str,
        payload: Any,
        confidence: float = 1.0,
        latency: int = 0,
        processing_time: int = 0,
        data_version: str = "1.0.0",
        retry_count: int = 0,
        timestamp: datetime | None = None,
        event_id: UUID | None = None,
    ) -> "BusEvent":
        """Factory for creating a new event with auto-filled metadata."""
        return cls(
            eventId=event_id or uuid4(),
            eventType=event_type,
            timestamp=timestamp or datetime.now(timezone.utc),
            provider=provider,
            latency=latency,
            confidence=confidence,
            dataVersion=data_version,
            retryCount=retry_count,
            agentId=agent_id,
            processingTime=processing_time,
            payload=payload,
        )


class BusClient(ABC):
    """Abstract bus client. Implementations: InMemoryBusClient, RedisBusClient."""

    @abstractmethod
    async def publish(self, event: BusEvent) -> None:
        """Publish an event. Validates 10 mandatory fields first."""

    @abstractmethod
    async def subscribe(self, pattern: str, handler: EventHandler) -> None:
        """Subscribe to events matching a glob pattern (e.g., 'market:*')."""

    @abstractmethod
    async def unsubscribe(self, pattern: str, handler: EventHandler) -> None:
        """Unsubscribe a handler from a pattern."""

    @abstractmethod
    async def close(self) -> None:
        """Clean up resources."""

    @abstractmethod
    async def health_check(self) -> bool:
        """Return True if the bus is connected and healthy."""


def pattern_matches(pattern: str, event_type: str) -> bool:
    """Glob pattern match for event types.

    '*' matches everything.
    'market:*' matches 'market:quote-updated' but not 'ta:signal-emitted'.
    'market:quote-updated' matches only itself.
    """
    if pattern == "*":
        return True
    if "*" not in pattern:
        return pattern == event_type
    # Convert glob to prefix match
    prefix = pattern.split("*")[0]
    return event_type.startswith(prefix)
