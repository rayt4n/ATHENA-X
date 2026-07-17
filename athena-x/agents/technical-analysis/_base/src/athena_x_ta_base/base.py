"""Base TA agent - Stage 7 req.

Every TA agent:
  1. Reads from Canonical Repository (via MarketRepository)
  2. Uses shared Bar Cache
  3. Emits ai:technical:* events
  4. Includes confidence score
  5. Never writes to database directly
  6. Never calls other TA agents directly (coordination via Event Bus)
"""
from __future__ import annotations
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from athena_x_runtime_event_envelope import EventEnvelope, create_event, EventPriority
from athena_x_runtime_logger import get_logger

from .timeframes import Timeframe, TimeframeContext
from .bar_cache import BarCache, CachedBars


@dataclass
class TAConfidence:
    """Confidence metadata for TA outputs."""
    score: float = 1.0  # 0..1
    quality: str = "A+"  # A+, A, B, C, D, F
    evidence: list[str] = field(default_factory=list)
    sources: int = 1

    @classmethod
    def from_score(cls, score: float) -> "TAConfidence":
        if score >= 0.99:
            quality = "A+"
        elif score >= 0.95:
            quality = "A"
        elif score >= 0.80:
            quality = "B"
        elif score >= 0.60:
            quality = "C"
        elif score >= 0.30:
            quality = "D"
        else:
            quality = "F"
        return cls(score=score, quality=quality)


@dataclass
class TAOutput:
    """Standard TA output - published as ai:technical:* event."""
    agent: str
    symbol: str
    timeframe: str
    indicator: str
    value: Any
    confidence: TAConfidence = field(default_factory=TAConfidence)
    calculation_time_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_event_payload(self) -> dict:
        """Convert to event payload for ai:technical:* events."""
        return {
            "agent": self.agent,
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "indicator": self.indicator,
            "value": self.value,
            "confidence": self.confidence.score,
            "quality": self.confidence.quality,
            "calculation_time_ms": self.calculation_time_ms,
            "evidence": self.confidence.evidence,
            "sources": self.confidence.sources,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


class BaseTAAgent(ABC):
    """Abstract base class for all Technical Analysis agents.

    Stage 7 rules:
      - Reads from Canonical Repository ONLY
      - Never writes to database
      - Emits ai:technical:* events
      - Never calls other TA agents directly
      - Uses shared Bar Cache
      - Uses shared Timeframe Context
    """

    def __init__(
        self,
        name: str,
        layer: int,
        bar_cache: BarCache | None = None,
        timeframe_context: TimeframeContext | None = None,
    ):
        self.name = name
        self.layer = layer
        self._bar_cache = bar_cache or BarCache()
        self._timeframe_context = timeframe_context or TimeframeContext()
        self._calculation_count = 0
        self._error_count = 0
        self._last_calculation: datetime | None = None
        self._total_calculation_time_ms = 0.0

    @property
    def agent_id(self) -> str:
        return f"ta.{self.name}"

    @abstractmethod
    async def compute(
        self,
        symbol: str,
        timeframe: Timeframe,
        repo: Any,
    ) -> TAOutput:
        """Compute the TA value for a symbol+timeframe.

        Args:
            symbol: canonical symbol (e.g., "SPY")
            timeframe: which timeframe to compute
            repo: MarketRepository (read-only access)

        Returns:
            TAOutput with value + confidence.
        """
        ...

    async def compute_and_publish(
        self,
        symbol: str,
        timeframe: Timeframe,
        repo: Any,
        event_bus: Any = None,
    ) -> TAOutput:
        """Compute + publish event on the bus."""
        start = time.monotonic()

        try:
            output = await self.compute(symbol, timeframe, repo)
            elapsed_ms = (time.monotonic() - start) * 1000
            output.calculation_time_ms = elapsed_ms

            self._calculation_count += 1
            self._total_calculation_time_ms += elapsed_ms
            self._last_calculation = datetime.now(timezone.utc)

            # Publish event
            if event_bus is not None:
                event = create_event(
                    event_type=f"ai:technical:{self.name}",
                    source_agent=self.agent_id,
                    symbol=symbol,
                    priority=EventPriority.NORMAL,
                    payload=output.to_event_payload(),
                    processing_time_ms=int(elapsed_ms),
                )
                await event_bus.publish(event)

            return output

        except Exception as e:
            self._error_count += 1
            raise

    def get_health(self) -> dict:
        """Return agent health for the Technical Supervisor."""
        avg_time = (
            self._total_calculation_time_ms / self._calculation_count
            if self._calculation_count > 0 else 0.0
        )
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "layer": self.layer,
            "running": self._last_calculation is not None,
            "calculation_count": self._calculation_count,
            "error_count": self._error_count,
            "avg_calculation_time_ms": avg_time,
            "last_calculation": self._last_calculation.isoformat() if self._last_calculation else None,
        }
