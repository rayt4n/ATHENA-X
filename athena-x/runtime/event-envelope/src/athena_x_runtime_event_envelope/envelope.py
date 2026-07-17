"""Standard event envelope - Stage 6 req 2.

Every event has the same structure:
{
  "event_id": "uuid",
  "event_type": "market:raw",
  "source_agent": "data-collection.yahoo",
  "correlation_id": "uuid",
  "symbol": "ES",
  "timestamp": "2026-07-18T09:30:01.250Z",
  "schema_version": "1.0.0",
  "priority": "high",
  "processing_time_ms": 5,
  "payload": {}
}

This makes debugging, replay, and tracing much easier.
"""
from __future__ import annotations
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID, uuid4
from pydantic import BaseModel, ConfigDict, Field, field_validator


ENVELOPE_SCHEMA_VERSION = "1.0.0"


class EventPriority(str, Enum):
    """4 priority levels (Stage 6 req 3)."""
    CRITICAL = "critical"  # Provider failure, trading halt, market disconnect
    HIGH = "high"          # ES tick, option flow, VIX update
    NORMAL = "normal"      # News, earnings, macro
    LOW = "low"            # Health checks, logs, metrics


class EventCategory(str, Enum):
    """5 event categories (Stage 6 req 1)."""
    MARKET = "market"
    OPTIONS = "options"
    NEWS = "news"
    AI = "ai"
    REPORTS = "reports"
    SYSTEM = "system"

    @classmethod
    def from_event_type(cls, event_type: str) -> "EventCategory":
        """Parse category from event type, handling aliases."""
        prefix = event_type.split(":")[0]
        # Handle 'report' -> 'reports' alias
        if prefix == "report":
            return cls.REPORTS
        return cls(prefix)


class EventEnvelope(BaseModel):
    """Standard event envelope - every event in ATHENA-X uses this structure.

    Stage 6 rule: No direct agent-to-agent calls. Everything communicates
    through events with this envelope.
    """

    model_config = ConfigDict(populate_by_name=True)

    # 10 mandatory fields
    event_id: UUID = Field(default_factory=uuid4, alias="event_id")
    event_type: str = Field(min_length=1, alias="event_type")
    source_agent: str = Field(min_length=1, alias="source_agent")
    correlation_id: UUID = Field(default_factory=uuid4, alias="correlation_id")
    symbol: str | None = Field(default=None, alias="symbol")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), alias="timestamp")
    schema_version: str = Field(default=ENVELOPE_SCHEMA_VERSION, alias="schema_version")
    priority: EventPriority = Field(default=EventPriority.NORMAL, alias="priority")
    processing_time_ms: int = Field(default=0, ge=0, alias="processing_time_ms")
    payload: Any = Field(default_factory=dict, alias="payload")

    @field_validator("timestamp")
    @classmethod
    def must_be_utc(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("timestamp must be UTC-aware")
        return v

    @property
    def category(self) -> EventCategory:
        """Extract category from event_type (e.g., 'market:raw' -> 'market')."""
        return EventCategory.from_event_type(self.event_type)

    def with_correlation(self, correlation_id: UUID) -> "EventEnvelope":
        """Create a child event that shares the correlation ID."""
        return EventEnvelope(
            event_id=uuid4(),
            event_type=self.event_type,
            source_agent=self.source_agent,
            correlation_id=correlation_id,
            symbol=self.symbol,
            timestamp=self.timestamp,
            schema_version=self.schema_version,
            priority=self.priority,
            processing_time_ms=self.processing_time_ms,
            payload=self.payload,
        )


def create_event(
    *,
    event_type: str,
    source_agent: str,
    payload: Any = None,
    symbol: str | None = None,
    priority: EventPriority = EventPriority.NORMAL,
    correlation_id: UUID | None = None,
    processing_time_ms: int = 0,
) -> EventEnvelope:
    """Factory for creating an event with auto-filled fields."""
    return EventEnvelope(
        event_id=uuid4(),
        event_type=event_type,
        source_agent=source_agent,
        correlation_id=correlation_id or uuid4(),
        symbol=symbol,
        timestamp=datetime.now(timezone.utc),
        schema_version=ENVELOPE_SCHEMA_VERSION,
        priority=priority,
        processing_time_ms=processing_time_ms,
        payload=payload,
    )
