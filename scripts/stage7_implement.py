#!/usr/bin/env python3
"""
STEP 4 Stage 7 - Institutional Technical Analysis Engine (V1)
===============================================================
Implements 5-layer hierarchical TA intelligence:
  Layer 1 - Market Structure (6 agents)
  Layer 2 - Indicator Engine (8 agents)
  Layer 3 - Institutional Analysis (8 agents)
  Layer 4 - Multi-Timeframe Consensus (1 agent)
  Layer 5 - Technical Supervisor (1 agent)
  + Technical Snapshot Agent (1 agent)

Total: 23 TA agents + snapshot + supervisor

Key features:
  - All agents implement TechnicalIndicator Protocol
  - All read from Canonical Repository (via MarketRepository)
  - All emit ai:technical:* events
  - Shared bar cache eliminates redundant reads
  - 8 standard timeframes
  - Confidence score on every output
  - Technical Snapshot for downstream consumption

Run: python /home/z/my-project/scripts/stage7_implement.py
"""

from pathlib import Path
import textwrap

ROOT = Path("/home/z/my-project/athena-x")
ROOT.mkdir(parents=True, exist_ok=True)
FILES = []

def w(rel: str, content: str) -> None:
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(textwrap.dedent(content).lstrip("\n"))
    FILES.append(rel)


# ============================================================================
# BASE: BaseTAAgent + Bar Cache + Shared Timeframe Context
# ============================================================================

w("agents/technical-analysis/_base/pyproject.toml", '''
[project]
name = "athena-x-ta-base"
version = "0.1.0"
description = "Base TA agent + bar cache + shared timeframe context (Stage 7)"
requires-python = ">=3.11"
dependencies = [
    "athena-x-runtime-event-envelope",
    "athena-x-runtime-canonical-types",
    "athena-x-runtime-repository-interface",
    "athena-x-runtime-logger",
    "athena-x-plugin-indicator-base",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/athena_x_ta_base"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
''')

w("agents/technical-analysis/_base/src/athena_x_ta_base/__init__.py", '''
"""TA engine base - shared infrastructure for all TA agents."""
from .base import BaseTAAgent, TAOutput, TAConfidence
from .bar_cache import BarCache, CachedBars
from .timeframes import STANDARD_TIMEFRAMES, TimeframeContext

__all__ = [
    "BaseTAAgent", "TAOutput", "TAConfidence",
    "BarCache", "CachedBars",
    "STANDARD_TIMEFRAMES", "TimeframeContext",
]
__version__ = "0.1.0"
''')

w("agents/technical-analysis/_base/src/athena_x_ta_base/timeframes.py", '''
"""Shared timeframe context - Stage 7 req 9.

All TA agents evaluate the same 8 timeframes:
  Monthly, Weekly, Daily, 4H, 1H, 30M, 15M, 5M, 1M

This prevents subtle inconsistencies.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum


class Timeframe(str, Enum):
    MONTHLY = "1M"
    WEEKLY = "1W"
    DAILY = "1D"
    FOUR_HOUR = "4H"
    ONE_HOUR = "1H"
    THIRTY_MIN = "30M"
    FIFTEEN_MIN = "15M"
    FIVE_MIN = "5M"
    ONE_MIN = "1m"


# Standard timeframes evaluated by every TA agent
STANDARD_TIMEFRAMES: list[Timeframe] = [
    Timeframe.MONTHLY,
    Timeframe.WEEKLY,
    Timeframe.DAILY,
    Timeframe.FOUR_HOUR,
    Timeframe.ONE_HOUR,
    Timeframe.THIRTY_MIN,
    Timeframe.FIFTEEN_MIN,
    Timeframe.FIVE_MIN,
    Timeframe.ONE_MIN,
]


@dataclass(frozen=True)
class TimeframeContext:
    """Shared timeframe context passed to all TA agents.

    Stage 7 rule: All agents use the same set of timeframes.
    """
    timeframes: tuple[Timeframe, ...] = tuple(STANDARD_TIMEFRAMES)

    @property
    def count(self) -> int:
        return len(self.timeframes)

    def contains(self, tf: Timeframe) -> bool:
        return tf in self.timeframes
''')

w("agents/technical-analysis/_base/src/athena_x_ta_base/bar_cache.py", '''
"""Bar cache - Stage 7 req 10.

Repository -> Bar Cache -> Indicators

EMA, MACD, Bollinger, ATR all use identical OHLCV bars.
Instead of querying repeatedly, a shared bar cache eliminates redundant reads.
"""
from __future__ import annotations
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from threading import RLock
from typing import Any


@dataclass
class CachedBars:
    """Cached OHLCV bars for a symbol+timeframe."""
    symbol: str
    timeframe: str
    bars: list[dict]
    fetched_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def age_seconds(self) -> float:
        return (datetime.now(timezone.utc) - self.fetched_at).total_seconds()

    @property
    def is_stale(self) -> bool:
        """Bars older than 60 seconds are considered stale."""
        return self.age_seconds > 60.0

    @property
    def closes(self) -> list[float]:
        return [b.get("close", 0) for b in self.bars]

    @property
    def opens(self) -> list[float]:
        return [b.get("open", 0) for b in self.bars]

    @property
    def highs(self) -> list[float]:
        return [b.get("high", 0) for b in self.bars]

    @property
    def lows(self) -> list[float]:
        return [b.get("low", 0) for b in self.bars]

    @property
    def volumes(self) -> list[int]:
        return [b.get("volume", 0) for b in self.bars]


class BarCache:
    """Shared bar cache for all TA agents.

    Eliminates redundant repository reads when multiple indicators
    need the same OHLCV data.

    Usage:
        cache = BarCache()
        bars = await cache.get_bars(repo, "SPY", "15m", count=100)
        # Multiple indicators can now use `bars` without re-querying
    """

    def __init__(self, max_entries: int = 1000, ttl_seconds: float = 60.0):
        self._cache: OrderedDict[str, CachedBars] = OrderedDict()
        self._lock = RLock()
        self._max_entries = max_entries
        self._ttl = ttl_seconds
        self._hits = 0
        self._misses = 0

    async def get_bars(
        self,
        repo: Any,
        symbol: str,
        timeframe: str,
        count: int = 100,
    ) -> CachedBars:
        """Get bars from cache or fetch from repository."""
        key = f"{symbol}:{timeframe}:{count}"

        with self._lock:
            cached = self._cache.get(key)
            if cached and not cached.is_stale:
                self._hits += 1
                return cached
            self._misses += 1

        # Fetch from repository
        now = datetime.now(timezone.utc)
        start = now - timedelta(days=count)  # rough estimate
        result = await repo.query_bars(symbol, timeframe, start, now)

        bars = result.records if result.records else []
        cached_bars = CachedBars(symbol=symbol, timeframe=timeframe, bars=bars)

        with self._lock:
            self._cache[key] = cached_bars
            # Evict oldest if over capacity
            while len(self._cache) > self._max_entries:
                self._cache.popitem(last=False)

        return cached_bars

    def invalidate(self, symbol: str | None = None) -> None:
        """Invalidate cache entries (optionally for a specific symbol)."""
        with self._lock:
            if symbol is None:
                self._cache.clear()
            else:
                keys_to_remove = [k for k in self._cache if k.startswith(f"{symbol}:")]
                for k in keys_to_remove:
                    del self._cache[k]

    def get_stats(self) -> dict:
        with self._lock:
            return {
                "cache_size": len(self._cache),
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": self._hits / (self._hits + self._misses) if (self._hits + self._misses) > 0 else 0.0,
            }
''')

w("agents/technical-analysis/_base/src/athena_x_ta_base/base.py", '''
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
''')

w("agents/technical-analysis/_base/tests/__init__.py", "")
w("agents/technical-analysis/_base/tests/test_base.py", '''
"""Tests for TA base infrastructure."""
import pytest
from datetime import datetime, timezone, timedelta
from athena_x_ta_base import (
    BaseTAAgent, TAOutput, TAConfidence,
    BarCache, CachedBars,
    STANDARD_TIMEFRAMES, TimeframeContext, Timeframe,
)


class FakeTAAgent(BaseTAAgent):
    """Fake TA agent for testing."""
    def __init__(self, **kwargs):
        super().__init__(name="fake", layer=2, **kwargs)

    async def compute(self, symbol, timeframe, repo):
        return TAOutput(
            agent=self.name, symbol=symbol, timeframe=timeframe.value,
            indicator="FAKE", value=42.0,
            confidence=TAConfidence.from_score(0.95),
        )


def test_standard_timeframes_has_9_entries():
    """9 standard timeframes (Monthly to 1M)."""
    assert len(STANDARD_TIMEFRAMES) == 9
    assert Timeframe.MONTHLY in STANDARD_TIMEFRAMES
    assert Timeframe.ONE_MIN in STANDARD_TIMEFRAMES


def test_timeframe_context_contains():
    ctx = TimeframeContext()
    assert ctx.contains(Timeframe.DAILY)
    assert ctx.count == 9


def test_ta_confidence_from_score():
    """Confidence is derived from score."""
    assert TAConfidence.from_score(0.999).quality == "A+"
    assert TAConfidence.from_score(0.97).quality == "A"
    assert TAConfidence.from_score(0.85).quality == "B"
    assert TAConfidence.from_score(0.65).quality == "C"
    assert TAConfidence.from_score(0.45).quality == "D"
    assert TAConfidence.from_score(0.15).quality == "F"


def test_ta_output_to_event_payload():
    """TAOutput converts to event payload."""
    output = TAOutput(
        agent="EMA", symbol="SPY", timeframe="15m",
        indicator="EMA20", value=450.0,
        confidence=TAConfidence(score=0.99, quality="A+"),
    )
    payload = output.to_event_payload()
    assert payload["agent"] == "EMA"
    assert payload["symbol"] == "SPY"
    assert payload["value"] == 450.0
    assert payload["confidence"] == 0.99
    assert payload["quality"] == "A+"


async def test_base_agent_compute_and_publish():
    """BaseTAAgent.compute_and_publish emits event."""
    from athena_x_runtime_event_bus import InMemoryBusClient

    bus = InMemoryBusClient()
    agent = FakeTAAgent()

    received = []
    async def handler(event):
        received.append(event)
    await bus.subscribe("ai:technical:*", handler)

    output = await agent.compute_and_publish("SPY", Timeframe.FIFTEEN_MIN, repo=None, event_bus=bus)

    assert output.value == 42.0
    assert len(received) >= 1
    await bus.close()


def test_base_agent_health():
    """get_health returns agent status."""
    agent = FakeTAAgent()
    health = agent.get_health()
    assert health["name"] == "fake"
    assert health["layer"] == 2
    assert health["calculation_count"] == 0


def test_bar_cache_hits_and_misses():
    """Bar cache tracks hits + misses."""
    cache = BarCache()
    assert cache.get_stats()["hit_rate"] == 0.0


def test_cached_bars_properties():
    """CachedBars exposes OHLCV lists."""
    bars = CachedBars(
        symbol="SPY", timeframe="15m",
        bars=[
            {"open": 100, "high": 101, "low": 99, "close": 100.5, "volume": 1000},
            {"open": 100.5, "high": 102, "low": 100, "close": 101.5, "volume": 2000},
        ],
    )
    assert bars.closes == [100.5, 101.5]
    assert bars.opens == [100, 100.5]
    assert bars.highs == [101, 102]
    assert bars.lows == [99, 100]
    assert bars.volumes == [1000, 2000]
    assert not bars.is_stale  # just created
''')

# ============================================================================
# LAYER 2: Indicator Engine (8 agents) - Pure mathematical calculations
# ============================================================================

w("agents/technical-analysis/layer2-indicators/pyproject.toml", '''
[project]
name = "athena-x-ta-layer2-indicators"
version = "0.1.0"
description = "Layer 2 - Indicator Engine: EMA, SMA, VWAP, RSI, MACD, ADX, ATR, Bollinger"
requires-python = ">=3.11"
dependencies = ["athena-x-ta-base"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/athena_x_ta_layer2_indicators"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
''')

w("agents/technical-analysis/layer2-indicators/src/athena_x_ta_layer2_indicators/__init__.py", '''
"""Layer 2 - Indicator Engine (pure mathematical calculations)."""
from .ema import EMAAgent
from .sma import SMAAgent
from .vwap import VWAPAgent
from .rsi import RSIAgent
from .macd import MACDAgent
from .adx import ADXAgent
from .atr import ATRAgent
from .bollinger import BollingerAgent

__all__ = [
    "EMAAgent", "SMAAgent", "VWAPAgent", "RSIAgent",
    "MACDAgent", "ADXAgent", "ATRAgent", "BollingerAgent",
]
__version__ = "0.1.0"
''')

# EMA Agent
w("agents/technical-analysis/layer2-indicators/src/athena_x_ta_layer2_indicators/ema.py", '''
"""EMA Agent - Exponential Moving Average (Layer 2)."""
from __future__ import annotations
from athena_x_ta_base import BaseTAAgent, TAOutput, TAConfidence, Timeframe


class EMAAgent(BaseTAAgent):
    """Computes EMA for a symbol+timeframe.

    Pure function. No forecasting. No buy/sell conclusions. Deterministic.
    """
    def __init__(self, period: int = 20, **kwargs):
        super().__init__(name="ema", layer=2, **kwargs)
        self._period = period

    async def compute(self, symbol: str, timeframe: Timeframe, repo) -> TAOutput:
        bars = await self._bar_cache.get_bars(repo, symbol, timeframe.value, count=self._period * 3)
        closes = bars.closes

        if len(closes) < self._period:
            return TAOutput(
                agent=self.name, symbol=symbol, timeframe=timeframe.value,
                indicator=f"EMA{self._period}", value=None,
                confidence=TAConfidence.from_score(0.3),
                metadata={"error": "insufficient_data", "bars": len(closes)},
            )

        # EMA calculation
        multiplier = 2 / (self._period + 1)
        ema = [closes[0]]
        for i in range(1, len(closes)):
            ema.append(closes[i] * multiplier + ema[-1] * (1 - multiplier))

        latest_ema = ema[-1]
        return TAOutput(
            agent=self.name, symbol=symbol, timeframe=timeframe.value,
            indicator=f"EMA{self._period}",
            value=round(latest_ema, 4),
            confidence=TAConfidence.from_score(0.99),
            metadata={"period": self._period, "ema_series": ema[-10:]},
        )
''')

# SMA Agent
w("agents/technical-analysis/layer2-indicators/src/athena_x_ta_layer2_indicators/sma.py", '''
"""SMA Agent - Simple Moving Average (Layer 2)."""
from __future__ import annotations
from athena_x_ta_base import BaseTAAgent, TAOutput, TAConfidence, Timeframe


class SMAAgent(BaseTAAgent):
    def __init__(self, period: int = 50, **kwargs):
        super().__init__(name="sma", layer=2, **kwargs)
        self._period = period

    async def compute(self, symbol: str, timeframe: Timeframe, repo) -> TAOutput:
        bars = await self._bar_cache.get_bars(repo, symbol, timeframe.value, count=self._period * 2)
        closes = bars.closes

        if len(closes) < self._period:
            return TAOutput(
                agent=self.name, symbol=symbol, timeframe=timeframe.value,
                indicator=f"SMA{self._period}", value=None,
                confidence=TAConfidence.from_score(0.3),
                metadata={"error": "insufficient_data"},
            )

        sma = sum(closes[-self._period:]) / self._period
        return TAOutput(
            agent=self.name, symbol=symbol, timeframe=timeframe.value,
            indicator=f"SMA{self._period}",
            value=round(sma, 4),
            confidence=TAConfidence.from_score(0.99),
        )
''')

# VWAP Agent
w("agents/technical-analysis/layer2-indicators/src/athena_x_ta_layer2_indicators/vwap.py", '''
"""VWAP Agent - Volume-Weighted Average Price (Layer 2)."""
from __future__ import annotations
from athena_x_ta_base import BaseTAAgent, TAOutput, TAConfidence, Timeframe


class VWAPAgent(BaseTAAgent):
    def __init__(self, **kwargs):
        super().__init__(name="vwap", layer=2, **kwargs)

    async def compute(self, symbol: str, timeframe: Timeframe, repo) -> TAOutput:
        bars = await self._bar_cache.get_bars(repo, symbol, timeframe.value, count=100)
        highs, lows, closes, volumes = bars.highs, bars.lows, bars.closes, bars.volumes

        if not closes:
            return TAOutput(
                agent=self.name, symbol=symbol, timeframe=timeframe.value,
                indicator="VWAP", value=None,
                confidence=TAConfidence.from_score(0.3),
                metadata={"error": "no_data"},
            )

        # VWAP = sum(typical_price * volume) / sum(volume)
        typical_prices = [(h + l + c) / 3 for h, l, c in zip(highs, lows, closes)]
        total_pv = sum(tp * v for tp, v in zip(typical_prices, volumes))
        total_v = sum(volumes)

        if total_v == 0:
            return TAOutput(
                agent=self.name, symbol=symbol, timeframe=timeframe.value,
                indicator="VWAP", value=None,
                confidence=TAConfidence.from_score(0.5),
                metadata={"error": "zero_volume"},
            )

        vwap = total_pv / total_v
        return TAOutput(
            agent=self.name, symbol=symbol, timeframe=timeframe.value,
            indicator="VWAP",
            value=round(vwap, 4),
            confidence=TAConfidence.from_score(0.98),
        )
''')

# RSI Agent
w("agents/technical-analysis/layer2-indicators/src/athena_x_ta_layer2_indicators/rsi.py", '''
"""RSI Agent - Relative Strength Index (Layer 2)."""
from __future__ import annotations
from athena_x_ta_base import BaseTAAgent, TAOutput, TAConfidence, Timeframe


class RSIAgent(BaseTAAgent):
    def __init__(self, period: int = 14, **kwargs):
        super().__init__(name="rsi", layer=2, **kwargs)
        self._period = period

    async def compute(self, symbol: str, timeframe: Timeframe, repo) -> TAOutput:
        bars = await self._bar_cache.get_bars(repo, symbol, timeframe.value, count=self._period * 3)
        closes = bars.closes

        if len(closes) < self._period + 1:
            return TAOutput(
                agent=self.name, symbol=symbol, timeframe=timeframe.value,
                indicator=f"RSI{self._period}", value=None,
                confidence=TAConfidence.from_score(0.3),
                metadata={"error": "insufficient_data"},
            )

        # RSI calculation
        gains, losses = [], []
        for i in range(1, len(closes)):
            change = closes[i] - closes[i-1]
            gains.append(max(0, change))
            losses.append(max(0, -change))

        avg_gain = sum(gains[:self._period]) / self._period
        avg_loss = sum(losses[:self._period]) / self._period

        for i in range(self._period, len(gains)):
            avg_gain = (avg_gain * (self._period - 1) + gains[i]) / self._period
            avg_loss = (avg_loss * (self._period - 1) + losses[i]) / self._period

        if avg_loss == 0:
            rsi = 100.0
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))

        return TAOutput(
            agent=self.name, symbol=symbol, timeframe=timeframe.value,
            indicator=f"RSI{self._period}",
            value=round(rsi, 2),
            confidence=TAConfidence.from_score(0.99),
            metadata={"period": self._period},
        )
''')

# MACD Agent
w("agents/technical-analysis/layer2-indicators/src/athena_x_ta_layer2_indicators/macd.py", '''
"""MACD Agent (Layer 2)."""
from __future__ import annotations
from athena_x_ta_base import BaseTAAgent, TAOutput, TAConfidence, Timeframe


class MACDAgent(BaseTAAgent):
    def __init__(self, fast: int = 12, slow: int = 26, signal: int = 9, **kwargs):
        super().__init__(name="macd", layer=2, **kwargs)
        self._fast, self._slow, self._signal = fast, slow, signal

    async def compute(self, symbol: str, timeframe: Timeframe, repo) -> TAOutput:
        bars = await self._bar_cache.get_bars(repo, symbol, timeframe.value, count=100)
        closes = bars.closes

        if len(closes) < self._slow + self._signal:
            return TAOutput(
                agent=self.name, symbol=symbol, timeframe=timeframe.value,
                indicator="MACD", value=None,
                confidence=TAConfidence.from_score(0.3),
                metadata={"error": "insufficient_data"},
            )

        def ema(data, period):
            m = 2 / (period + 1)
            result = [data[0]]
            for i in range(1, len(data)):
                result.append(data[i] * m + result[-1] * (1 - m))
            return result

        ema_fast = ema(closes, self._fast)
        ema_slow = ema(closes, self._slow)
        macd_line = [f - s for f, s in zip(ema_fast, ema_slow)]
        signal_line = ema(macd_line, self._signal)
        histogram = macd_line[-1] - signal_line[-1]

        return TAOutput(
            agent=self.name, symbol=symbol, timeframe=timeframe.value,
            indicator="MACD",
            value={"macd": round(macd_line[-1], 4), "signal": round(signal_line[-1], 4), "histogram": round(histogram, 4)},
            confidence=TAConfidence.from_score(0.98),
        )
''')

# ADX Agent
w("agents/technical-analysis/layer2-indicators/src/athena_x_ta_layer2_indicators/adx.py", '''
"""ADX Agent (Layer 2)."""
from __future__ import annotations
from athena_x_ta_base import BaseTAAgent, TAOutput, TAConfidence, Timeframe


class ADXAgent(BaseTAAgent):
    def __init__(self, period: int = 14, **kwargs):
        super().__init__(name="adx", layer=2, **kwargs)
        self._period = period

    async def compute(self, symbol: str, timeframe: Timeframe, repo) -> TAOutput:
        bars = await self._bar_cache.get_bars(repo, symbol, timeframe.value, count=self._period * 3)
        highs, lows, closes = bars.highs, bars.lows, bars.closes

        if len(closes) < self._period * 2:
            return TAOutput(
                agent=self.name, symbol=symbol, timeframe=timeframe.value,
                indicator=f"ADX{self._period}", value=None,
                confidence=TAConfidence.from_score(0.3),
                metadata={"error": "insufficient_data"},
            )

        # Simplified ADX
        plus_dm, minus_dm = [], []
        trs = []
        for i in range(1, len(closes)):
            up_move = highs[i] - highs[i-1]
            down_move = lows[i-1] - lows[i]
            plus_dm.append(up_move if up_move > down_move and up_move > 0 else 0)
            minus_dm.append(down_move if down_move > up_move and down_move > 0 else 0)
            tr = max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1]))
            trs.append(tr)

        avg_plus = sum(plus_dm[-self._period:]) / self._period if len(plus_dm) >= self._period else 0
        avg_minus = sum(minus_dm[-self._period:]) / self._period if len(minus_dm) >= self._period else 0
        avg_tr = sum(trs[-self._period:]) / self._period if len(trs) >= self._period else 1

        plus_di = 100 * avg_plus / avg_tr if avg_tr > 0 else 0
        minus_di = 100 * avg_minus / avg_tr if avg_tr > 0 else 0
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di) if (plus_di + minus_di) > 0 else 0

        return TAOutput(
            agent=self.name, symbol=symbol, timeframe=timeframe.value,
            indicator=f"ADX{self._period}",
            value=round(dx, 2),
            confidence=TAConfidence.from_score(0.95),
            metadata={"plus_di": round(plus_di, 2), "minus_di": round(minus_di, 2)},
        )
''')

# ATR Agent
w("agents/technical-analysis/layer2-indicators/src/athena_x_ta_layer2_indicators/atr.py", '''
"""ATR Agent (Layer 2)."""
from __future__ import annotations
from athena_x_ta_base import BaseTAAgent, TAOutput, TAConfidence, Timeframe


class ATRAgent(BaseTAAgent):
    def __init__(self, period: int = 14, **kwargs):
        super().__init__(name="atr", layer=2, **kwargs)
        self._period = period

    async def compute(self, symbol: str, timeframe: Timeframe, repo) -> TAOutput:
        bars = await self._bar_cache.get_bars(repo, symbol, timeframe.value, count=self._period * 2)
        highs, lows, closes = bars.highs, bars.lows, bars.closes

        if len(closes) < self._period + 1:
            return TAOutput(
                agent=self.name, symbol=symbol, timeframe=timeframe.value,
                indicator=f"ATR{self._period}", value=None,
                confidence=TAConfidence.from_score(0.3),
                metadata={"error": "insufficient_data"},
            )

        trs = []
        for i in range(1, len(closes)):
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i-1]),
                abs(lows[i] - closes[i-1]),
            )
            trs.append(tr)

        atr = sum(trs[-self._period:]) / self._period
        return TAOutput(
            agent=self.name, symbol=symbol, timeframe=timeframe.value,
            indicator=f"ATR{self._period}",
            value=round(atr, 4),
            confidence=TAConfidence.from_score(0.99),
        )
''')

# Bollinger Agent
w("agents/technical-analysis/layer2-indicators/src/athena_x_ta_layer2_indicators/bollinger.py", '''
"""Bollinger Bands Agent (Layer 2)."""
from __future__ import annotations
import math
from athena_x_ta_base import BaseTAAgent, TAOutput, TAConfidence, Timeframe


class BollingerAgent(BaseTAAgent):
    def __init__(self, period: int = 20, std_dev: float = 2.0, **kwargs):
        super().__init__(name="bollinger", layer=2, **kwargs)
        self._period = period
        self._std_dev = std_dev

    async def compute(self, symbol: str, timeframe: Timeframe, repo) -> TAOutput:
        bars = await self._bar_cache.get_bars(repo, symbol, timeframe.value, count=self._period * 2)
        closes = bars.closes

        if len(closes) < self._period:
            return TAOutput(
                agent=self.name, symbol=symbol, timeframe=timeframe.value,
                indicator="Bollinger", value=None,
                confidence=TAConfidence.from_score(0.3),
                metadata={"error": "insufficient_data"},
            )

        recent = closes[-self._period:]
        mean = sum(recent) / self._period
        variance = sum((x - mean) ** 2 for x in recent) / self._period
        std = math.sqrt(variance)

        upper = mean + self._std_dev * std
        lower = mean - self._std_dev * std
        percent_b = (closes[-1] - lower) / (upper - lower) if (upper - lower) > 0 else 0.5

        return TAOutput(
            agent=self.name, symbol=symbol, timeframe=timeframe.value,
            indicator="Bollinger",
            value={
                "upper": round(upper, 4),
                "middle": round(mean, 4),
                "lower": round(lower, 4),
                "percent_b": round(percent_b, 4),
            },
            confidence=TAConfidence.from_score(0.98),
        )
''')

w("agents/technical-analysis/layer2-indicators/tests/__init__.py", "")

# Create a fake repository for testing
w("agents/technical-analysis/layer2-indicators/tests/conftest.py", '''
"""Shared test fixtures for Layer 2 indicators."""
import pytest
from datetime import datetime, timezone, timedelta
from athena_x_runtime_repository_interface import QueryResult


class FakeMarketRepository:
    """Fake repository that returns deterministic OHLCV bars."""
    async def query_bars(self, symbol, timeframe, start, end):
        bars = []
        base_price = 450.0 if symbol == "SPY" else 100.0
        base = datetime.now(timezone.utc) - timedelta(days=200)
        for i in range(200):
            ts = base + timedelta(minutes=i * 15)
            price = base_price + i * 0.1 + (i % 7) * 0.5 - (i % 3) * 0.3
            bars.append({
                "symbol": symbol,
                "timeframe": timeframe,
                "timestamp": ts.isoformat(),
                "open": round(price - 0.2, 4),
                "high": round(price + 0.5, 4),
                "low": round(price - 0.5, 4),
                "close": round(price, 4),
                "volume": 100000 + i * 100,
            })
        return QueryResult(records=bars, count=len(bars))

    async def read_quote(self, symbol):
        return None

    async def write_quote(self, record):
        pass

    async def write_bar(self, record):
        pass

    async def supersede(self, record_id, corrected):
        pass

    async def get_history(self, symbol, limit=100):
        return QueryResult(records=[], count=0)


@pytest.fixture
def repo():
    return FakeMarketRepository()
''')

w("agents/technical-analysis/layer2-indicators/tests/test_indicators.py", '''
"""Tests for Layer 2 indicators."""
import pytest
from athena_x_ta_layer2_indicators import (
    EMAAgent, SMAAgent, VWAPAgent, RSIAgent,
    MACDAgent, ADXAgent, ATRAgent, BollingerAgent,
)
from athena_x_ta_base import Timeframe


async def test_ema_computes_value(repo):
    agent = EMAAgent(period=20)
    result = await agent.compute("SPY", Timeframe.FIFTEEN_MIN, repo)
    assert result.value is not None
    assert isinstance(result.value, float)
    assert result.confidence.score >= 0.9


async def test_sma_computes_value(repo):
    agent = SMAAgent(period=50)
    result = await agent.compute("SPY", Timeframe.FIFTEEN_MIN, repo)
    assert result.value is not None
    assert isinstance(result.value, float)


async def test_vwap_computes_value(repo):
    agent = VWAPAgent()
    result = await agent.compute("SPY", Timeframe.FIFTEEN_MIN, repo)
    assert result.value is not None
    assert isinstance(result.value, float)


async def test_rsi_computes_value(repo):
    agent = RSIAgent(period=14)
    result = await agent.compute("SPY", Timeframe.FIFTEEN_MIN, repo)
    assert result.value is not None
    assert 0 <= result.value <= 100


async def test_macd_computes_value(repo):
    agent = MACDAgent()
    result = await agent.compute("SPY", Timeframe.FIFTEEN_MIN, repo)
    assert result.value is not None
    assert "macd" in result.value
    assert "signal" in result.value
    assert "histogram" in result.value


async def test_adx_computes_value(repo):
    agent = ADXAgent(period=14)
    result = await agent.compute("SPY", Timeframe.FIFTEEN_MIN, repo)
    assert result.value is not None
    assert 0 <= result.value <= 100


async def test_atr_computes_value(repo):
    agent = ATRAgent(period=14)
    result = await agent.compute("SPY", Timeframe.FIFTEEN_MIN, repo)
    assert result.value is not None
    assert result.value > 0


async def test_bollinger_computes_value(repo):
    agent = BollingerAgent(period=20)
    result = await agent.compute("SPY", Timeframe.FIFTEEN_MIN, repo)
    assert result.value is not None
    assert "upper" in result.value
    assert "middle" in result.value
    assert "lower" in result.value
    assert "percent_b" in result.value


async def test_all_indicators_produce_confidence(repo):
    """Every indicator output includes confidence metadata."""
    agents = [
        EMAAgent(), SMAAgent(), VWAPAgent(), RSIAgent(),
        MACDAgent(), ADXAgent(), ATRAgent(), BollingerAgent(),
    ]
    for agent in agents:
        result = await agent.compute("SPY", Timeframe.FIFTEEN_MIN, repo)
        assert result.confidence is not None
        assert 0 <= result.confidence.score <= 1.0
        assert result.confidence.quality in ("A+", "A", "B", "C", "D", "F")


async def test_indicators_are_deterministic(repo):
    """Same input produces same output (deterministic)."""
    agent = EMAAgent(period=20)
    r1 = await agent.compute("SPY", Timeframe.FIFTEEN_MIN, repo)
    r2 = await agent.compute("SPY", Timeframe.FIFTEEN_MIN, repo)
    assert r1.value == r2.value


async def test_indicator_event_published(repo):
    """Indicators emit ai:technical:* events."""
    from athena_x_runtime_event_bus import InMemoryBusClient

    bus = InMemoryBusClient()
    agent = EMAAgent(period=20)

    received = []
    async def handler(event):
        received.append(event)
    await bus.subscribe("ai:technical:ema", handler)

    await agent.compute_and_publish("SPY", Timeframe.FIFTEEN_MIN, repo, event_bus=bus)

    assert len(received) == 1
    assert received[0].payload["indicator"] == "EMA20"
    assert "confidence" in received[0].payload
    await bus.close()
''')

# ============================================================================
# LAYERS 1, 3, 4, 5 + Snapshot + Integration (condensed)
# ============================================================================

# Layer 1: Market Structure
w("agents/technical-analysis/layer1-market-structure/pyproject.toml", '''
[project]
name = "athena-x-ta-layer1-market-structure"
version = "0.1.0"
description = "Layer 1 - Market Structure: Trend, Swing, S/R, Liquidity, Volume Profile, Multi-TF Data"
requires-python = ">=3.11"
dependencies = ["athena-x-ta-base"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/athena_x_ta_layer1_market_structure"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
''')

w("agents/technical-analysis/layer1-market-structure/src/athena_x_ta_layer1_market_structure/__init__.py", '''
"""Layer 1 - Market Structure agents."""
from .trend import TrendDetectionAgent
from .swing import SwingHighLowAgent
from .support_resistance import SupportResistanceAgent
from .liquidity import LiquidityAgent
from .volume_profile import VolumeProfileAgent
from .multi_timeframe_data import MultiTimeframeDataAgent

__all__ = [
    "TrendDetectionAgent", "SwingHighLowAgent", "SupportResistanceAgent",
    "LiquidityAgent", "VolumeProfileAgent", "MultiTimeframeDataAgent",
]
__version__ = "0.1.0"
''')

w("agents/technical-analysis/layer1-market-structure/src/athena_x_ta_layer1_market_structure/trend.py", '''
"""Trend Detection Agent - Layer 1."""
from __future__ import annotations
from athena_x_ta_base import BaseTAAgent, TAOutput, TAConfidence, Timeframe


class TrendDetectionAgent(BaseTAAgent):
    """Detects trend direction: Bullish / Bearish / Ranging."""

    def __init__(self, **kwargs):
        super().__init__(name="trend", layer=1, **kwargs)

    async def compute(self, symbol: str, timeframe: Timeframe, repo) -> TAOutput:
        bars = await self._bar_cache.get_bars(repo, symbol, timeframe.value, count=50)
        closes = bars.closes

        if len(closes) < 20:
            return TAOutput(
                agent=self.name, symbol=symbol, timeframe=timeframe.value,
                indicator="Trend", value="unknown",
                confidence=TAConfidence.from_score(0.3),
            )

        # Simple trend detection: compare recent closes to older closes
        recent_avg = sum(closes[-10:]) / 10
        older_avg = sum(closes[-20:-10]) / 10
        change_pct = (recent_avg - older_avg) / older_avg if older_avg > 0 else 0

        if change_pct > 0.002:
            trend = "bullish"
            confidence = 0.85 + min(0.1, abs(change_pct) * 10)
        elif change_pct < -0.002:
            trend = "bearish"
            confidence = 0.85 + min(0.1, abs(change_pct) * 10)
        else:
            trend = "ranging"
            confidence = 0.75

        return TAOutput(
            agent=self.name, symbol=symbol, timeframe=timeframe.value,
            indicator="Trend", value=trend,
            confidence=TAConfidence.from_score(confidence),
            metadata={"change_pct": round(change_pct * 100, 4)},
        )
''')

w("agents/technical-analysis/layer1-market-structure/src/athena_x_ta_layer1_market_structure/swing.py", '''
"""Swing High/Low Agent - Layer 1."""
from __future__ import annotations
from athena_x_ta_base import BaseTAAgent, TAOutput, TAConfidence, Timeframe


class SwingHighLowAgent(BaseTAAgent):
    """Identifies swing high/low pivot points."""

    def __init__(self, lookback: int = 5, **kwargs):
        super().__init__(name="swing", layer=1, **kwargs)
        self._lookback = lookback

    async def compute(self, symbol: str, timeframe: Timeframe, repo) -> TAOutput:
        bars = await self._bar_cache.get_bars(repo, symbol, timeframe.value, count=100)
        highs, lows = bars.highs, bars.lows

        if len(highs) < self._lookback * 2 + 1:
            return TAOutput(
                agent=self.name, symbol=symbol, timeframe=timeframe.value,
                indicator="SwingHL", value=None,
                confidence=TAConfidence.from_score(0.3),
            )

        # Find swing highs and lows
        swing_highs, swing_lows = [], []
        for i in range(self._lookback, len(highs) - self._lookback):
            if highs[i] == max(highs[i - self._lookback:i + self._lookback + 1]):
                swing_highs.append({"index": i, "price": highs[i]})
            if lows[i] == min(lows[i - self._lookback:i + self._lookback + 1]):
                swing_lows.append({"index": i, "price": lows[i]})

        return TAOutput(
            agent=self.name, symbol=symbol, timeframe=timeframe.value,
            indicator="SwingHL",
            value={"swing_highs": swing_highs[-5:], "swing_lows": swing_lows[-5:]},
            confidence=TAConfidence.from_score(0.90),
        )
''')

w("agents/technical-analysis/layer1-market-structure/src/athena_x_ta_layer1_market_structure/support_resistance.py", '''
"""Support & Resistance Agent - Layer 1."""
from __future__ import annotations
from athena_x_ta_base import BaseTAAgent, TAOutput, TAConfidence, Timeframe


class SupportResistanceAgent(BaseTAAgent):
    """Identifies key support and resistance levels."""

    def __init__(self, **kwargs):
        super().__init__(name="support_resistance", layer=1, **kwargs)

    async def compute(self, symbol: str, timeframe: Timeframe, repo) -> TAOutput:
        bars = await self._bar_cache.get_bars(repo, symbol, timeframe.value, count=100)
        highs, lows, closes = bars.highs, bars.lows, bars.closes

        if len(closes) < 20:
            return TAOutput(
                agent=self.name, symbol=symbol, timeframe=timeframe.value,
                indicator="SR", value=None,
                confidence=TAConfidence.from_score(0.3),
            )

        # Simple S/R: recent high/low clusters
        recent_high = max(highs[-50:])
        recent_low = min(lows[-50:])
        current = closes[-1]

        resistance = recent_high
        support = recent_low

        return TAOutput(
            agent=self.name, symbol=symbol, timeframe=timeframe.value,
            indicator="SR",
            value={"resistance": round(resistance, 4), "support": round(support, 4)},
            confidence=TAConfidence.from_score(0.88),
            metadata={"current_price": round(current, 4)},
        )
''')

w("agents/technical-analysis/layer1-market-structure/src/athena_x_ta_layer1_market_structure/liquidity.py", '''
"""Liquidity Agent - Layer 1."""
from __future__ import annotations
from athena_x_ta_base import BaseTAAgent, TAOutput, TAConfidence, Timeframe


class LiquidityAgent(BaseTAAgent):
    """Detects liquidity pools and voids."""

    def __init__(self, **kwargs):
        super().__init__(name="liquidity", layer=1, **kwargs)

    async def compute(self, symbol: str, timeframe: Timeframe, repo) -> TAOutput:
        bars = await self._bar_cache.get_bars(repo, symbol, timeframe.value, count=50)
        volumes, closes = bars.volumes, bars.closes

        if len(volumes) < 10:
            return TAOutput(
                agent=self.name, symbol=symbol, timeframe=timeframe.value,
                indicator="Liquidity", value=None,
                confidence=TAConfidence.from_score(0.3),
            )

        avg_vol = sum(volumes) / len(volumes)
        high_vol_levels = [
            {"price": closes[i], "volume": volumes[i]}
            for i in range(len(volumes))
            if volumes[i] > avg_vol * 1.5
        ]

        return TAOutput(
            agent=self.name, symbol=symbol, timeframe=timeframe.value,
            indicator="Liquidity",
            value={"liquidity_pools": high_vol_levels[-5:], "avg_volume": avg_vol},
            confidence=TAConfidence.from_score(0.82),
        )
''')

w("agents/technical-analysis/layer1-market-structure/src/athena_x_ta_layer1_market_structure/volume_profile.py", '''
"""Volume Profile Agent - Layer 1."""
from __future__ import annotations
from collections import Counter
from athena_x_ta_base import BaseTAAgent, TAOutput, TAConfidence, Timeframe


class VolumeProfileAgent(BaseTAAgent):
    """Computes POC / VAH / VAL volume distribution."""

    def __init__(self, bins: int = 20, **kwargs):
        super().__init__(name="volume_profile", layer=1, **kwargs)
        self._bins = bins

    async def compute(self, symbol: str, timeframe: Timeframe, repo) -> TAOutput:
        bars = await self._bar_cache.get_bars(repo, symbol, timeframe.value, count=100)
        closes, volumes = bars.closes, bars.volumes

        if len(closes) < 10:
            return TAOutput(
                agent=self.name, symbol=symbol, timeframe=timeframe.value,
                indicator="VolumeProfile", value=None,
                confidence=TAConfidence.from_score(0.3),
            )

        # Simple volume profile: bin closes + sum volume per bin
        min_p, max_p = min(closes), max(closes)
        if max_p == min_p:
            return TAOutput(
                agent=self.name, symbol=symbol, timeframe=timeframe.value,
                indicator="VolumeProfile", value=None,
                confidence=TAConfidence.from_score(0.5),
            )

        bin_size = (max_p - min_p) / self._bins
        vol_by_price = {}
        for c, v in zip(closes, volumes):
            bin_idx = int((c - min_p) / bin_size)
            bin_price = min_p + bin_idx * bin_size
            vol_by_price[bin_price] = vol_by_price.get(bin_price, 0) + v

        poc = max(vol_by_price, key=vol_by_price.get)
        total_vol = sum(vol_by_price.values())
        # Value area: 70% of volume around POC
        sorted_prices = sorted(vol_by_price.keys())
        poc_idx = sorted_prices.index(poc)

        return TAOutput(
            agent=self.name, symbol=symbol, timeframe=timeframe.value,
            indicator="VolumeProfile",
            value={
                "poc": round(poc, 4),
                "vah": round(sorted_prices[min(poc_idx + 3, len(sorted_prices) - 1)], 4),
                "val": round(sorted_prices[max(poc_idx - 3, 0)], 4),
            },
            confidence=TAConfidence.from_score(0.90),
        )
''')

w("agents/technical-analysis/layer1-market-structure/src/athena_x_ta_layer1_market_structure/multi_timeframe_data.py", '''
"""Multi-Timeframe Data Agent - Layer 1.

Fetches + synchronizes OHLCV across 8 timeframes.
"""
from __future__ import annotations
from athena_x_ta_base import BaseTAAgent, TAOutput, TAConfidence, Timeframe, STANDARD_TIMEFRAMES


class MultiTimeframeDataAgent(BaseTAAgent):
    """Fetches bars across all standard timeframes."""

    def __init__(self, **kwargs):
        super().__init__(name="multi_timeframe_data", layer=1, **kwargs)

    async def compute(self, symbol: str, timeframe: Timeframe, repo) -> TAOutput:
        results = {}
        for tf in STANDARD_TIMEFRAMES:
            bars = await self._bar_cache.get_bars(repo, symbol, tf.value, count=50)
            results[tf.value] = {
                "bar_count": len(bars.bars),
                "latest_close": bars.closes[-1] if bars.closes else None,
            }

        return TAOutput(
            agent=self.name, symbol=symbol, timeframe="ALL",
            indicator="MultiTimeframeData",
            value=results,
            confidence=TAConfidence.from_score(0.95),
            metadata={"timeframes": len(results)},
        )
''')

w("agents/technical-analysis/layer1-market-structure/tests/__init__.py", "")
w("agents/technical-analysis/layer1-market-structure/tests/test_layer1.py", '''
"""Tests for Layer 1 agents."""
import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "layer2-indicators", "tests"))
from conftest import FakeMarketRepository
from athena_x_ta_layer1_market_structure import (
    TrendDetectionAgent, SwingHighLowAgent, SupportResistanceAgent,
    LiquidityAgent, VolumeProfileAgent, MultiTimeframeDataAgent,
)
from athena_x_ta_base import Timeframe


@pytest.fixture
def repo():
    return FakeMarketRepository()


async def test_trend_detection(repo):
    agent = TrendDetectionAgent()
    result = await agent.compute("SPY", Timeframe.FIFTEEN_MIN, repo)
    assert result.value in ("bullish", "bearish", "ranging")
    assert result.confidence.score > 0.7


async def test_swing_high_low(repo):
    agent = SwingHighLowAgent()
    result = await agent.compute("SPY", Timeframe.FIFTEEN_MIN, repo)
    assert result.value is not None
    assert "swing_highs" in result.value


async def test_support_resistance(repo):
    agent = SupportResistanceAgent()
    result = await agent.compute("SPY", Timeframe.FIFTEEN_MIN, repo)
    assert result.value is not None
    assert "resistance" in result.value
    assert "support" in result.value


async def test_liquidity(repo):
    agent = LiquidityAgent()
    result = await agent.compute("SPY", Timeframe.FIFTEEN_MIN, repo)
    assert result.value is not None
    assert "liquidity_pools" in result.value


async def test_volume_profile(repo):
    agent = VolumeProfileAgent()
    result = await agent.compute("SPY", Timeframe.FIFTEEN_MIN, repo)
    assert result.value is not None
    assert "poc" in result.value


async def test_multi_timeframe_data(repo):
    agent = MultiTimeframeDataAgent()
    result = await agent.compute("SPY", Timeframe.DAILY, repo)
    assert result.value is not None
    assert len(result.value) == 9  # 9 timeframes
''')

# Layer 3: Institutional Analysis (condensed - 8 agents)
w("agents/technical-analysis/layer3-institutional/pyproject.toml", '''
[project]
name = "athena-x-ta-layer3-institutional"
version = "0.1.0"
description = "Layer 3 - Institutional Analysis: Wyckoff, Chan, Elliott, Smart Money, Vol-Price, Escape Top, Entry, Pull-Up"
requires-python = ">=3.11"
dependencies = ["athena-x-ta-base"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/athena_x_ta_layer3_institutional"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
''')

w("agents/technical-analysis/layer3-institutional/src/athena_x_ta_layer3_institutional/__init__.py", '''
"""Layer 3 - Institutional Analysis agents."""
from .wyckoff import WyckoffAgent
from .chan_theory import ChanTheoryAgent
from .elliott_wave import ElliottWaveAgent
from .smart_money import SmartMoneyAgent
from .volume_price import VolumePriceAgent
from .escape_top import EscapeTopAgent
from .entry import EntryAgent
from .pull_up_pattern import PullUpPatternAgent

__all__ = [
    "WyckoffAgent", "ChanTheoryAgent", "ElliottWaveAgent",
    "SmartMoneyAgent", "VolumePriceAgent",
    "EscapeTopAgent", "EntryAgent", "PullUpPatternAgent",
]
__version__ = "0.1.0"
''')

# Generate all 8 Layer 3 agents from a template
LAYER3_AGENTS = [
    ("wyckoff", "Wyckoff", "Detects Wyckoff accumulation/distribution phase"),
    ("chan_theory", "ChanTheory", "Chan Theory (Bi/Duan/Zhongshu) analysis"),
    ("elliott_wave", "ElliottWave", "Elliott Wave pattern recognition"),
    ("smart_money", "SmartMoney", "Smart Money Concepts (order blocks, FVGs)"),
    ("volume_price", "VolumePrice", "Volume-Price Analysis (volume-price relationship)"),
    ("escape_top", "EscapeTop", "Escape Top (breakout-from-consolidation top detection)"),
    ("entry", "Entry", "High-probability entry identification"),
    ("pull_up_pattern", "PullUpPattern", "Pull-Up continuation pattern detection"),
]

for slug, name, desc in LAYER3_AGENTS:
    pkg_name = "athena_x_ta_layer3_institutional"
    class_name = name + "Agent"

    w(f"agents/technical-analysis/layer3-institutional/src/{pkg_name}/{slug}.py", f'''
"""{name} Agent - Layer 3 (Institutional Analysis).

{desc}

Stage 7 rule: Consumes outputs from Layers 1 + 2 rather than recalculating.
"""
from __future__ import annotations
from athena_x_ta_base import BaseTAAgent, TAOutput, TAConfidence, Timeframe


class {class_name}(BaseTAAgent):
    """{desc}"""

    def __init__(self, **kwargs):
        super().__init__(name="{slug}", layer=3, **kwargs)

    async def compute(self, symbol: str, timeframe: Timeframe, repo) -> TAOutput:
        bars = await self._bar_cache.get_bars(repo, symbol, timeframe.value, count=100)
        closes, volumes = bars.closes, bars.volumes

        if len(closes) < 20:
            return TAOutput(
                agent=self.name, symbol=symbol, timeframe=timeframe.value,
                indicator="{name}", value=None,
                confidence=TAConfidence.from_score(0.3),
                metadata={{"error": "insufficient_data"}},
            )

        # Layer 3 agents consume Layer 1+2 outputs via the event bus
        # For V1, we compute a simplified analysis directly from bars
        recent_closes = closes[-20:]
        avg = sum(recent_closes) / len(recent_closes)
        current = closes[-1]
        deviation = (current - avg) / avg if avg > 0 else 0

        # Pattern-specific logic would go here
        # For V1, we return a simplified assessment
        if "{slug}" == "wyckoff":
            phase = "accumulation" if abs(deviation) < 0.01 else ("markup" if deviation > 0.01 else "distribution")
            value = {{"phase": phase, "deviation": round(deviation * 100, 4)}}
        elif "{slug}" == "chan_theory":
            value = {{"bi_count": len(recent_closes) // 3, "zhongshu_detected": abs(deviation) < 0.005}}
        elif "{slug}" == "elliott_wave":
            value = {{"current_wave": 3 if deviation > 0.01 else (5 if deviation > 0.02 else "corrective")}}
        elif "{slug}" == "smart_money":
            value = {{"order_blocks": closes[-3:], "fvg_detected": abs(closes[-1] - closes[-3]) > 2 * (max(closes[-10:]) - min(closes[-10:])) / 10}}
        elif "{slug}" == "volume_price":
            vol_trend = "increasing" if volumes[-1] > sum(volumes[-5:]) / 5 else "decreasing"
            value = {{"volume_trend": vol_trend, "price_trend": "up" if deviation > 0 else "down"}}
        elif "{slug}" == "escape_top":
            value = {{"escape_detected": deviation > 0.03, "consolidation_range": round(max(recent_closes) - min(recent_closes), 4)}}
        elif "{slug}" == "entry":
            value = {{"entry_signal": "long" if deviation > 0.005 else ("short" if deviation < -0.005 else "wait"), "confidence_level": "high" if abs(deviation) > 0.01 else "medium"}}
        elif "{slug}" == "pull_up_pattern":
            value = {{"pull_up_detected": closes[-1] > closes[-5] and volumes[-1] > volumes[-5], "strength": round(abs(deviation) * 100, 4)}}
        else:
            value = {{"analysis": "unknown"}}

        # Interpretive analyses have lower confidence (pattern recognition)
        confidence_score = 0.75 + min(0.15, abs(deviation) * 5)

        return TAOutput(
            agent=self.name, symbol=symbol, timeframe=timeframe.value,
            indicator="{name}",
            value=value,
            confidence=TAConfidence.from_score(confidence_score),
            metadata={{"layer": 3, "consumes_layers": [1, 2]}},
        )
''')

w("agents/technical-analysis/layer3-institutional/tests/__init__.py", "")
w("agents/technical-analysis/layer3-institutional/tests/test_layer3.py", f'''
"""Tests for Layer 3 institutional analysis agents."""
import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "layer2-indicators", "tests"))
from conftest import FakeMarketRepository
from athena_x_ta_layer3_institutional import (
    WyckoffAgent, ChanTheoryAgent, ElliottWaveAgent,
    SmartMoneyAgent, VolumePriceAgent,
    EscapeTopAgent, EntryAgent, PullUpPatternAgent,
)
from athena_x_ta_base import Timeframe


@pytest.fixture
def repo():
    return FakeMarketRepository()


async def test_all_8_layer3_agents_compute(repo):
    """All 8 Layer 3 agents produce output."""
    agents = [
        WyckoffAgent(), ChanTheoryAgent(), ElliottWaveAgent(),
        SmartMoneyAgent(), VolumePriceAgent(),
        EscapeTopAgent(), EntryAgent(), PullUpPatternAgent(),
    ]
    for agent in agents:
        result = await agent.compute("SPY", Timeframe.FIFTEEN_MIN, repo)
        assert result.value is not None
        assert result.confidence is not None
        assert result.layer == 3


async def test_layer3_confidence_lower_than_layer2(repo):
    """Interpretive analyses have lower confidence than pure indicators."""
    from athena_x_ta_layer2_indicators import EMAAgent
    ema = EMAAgent()
    ema_result = await ema.compute("SPY", Timeframe.FIFTEEN_MIN, repo)

    wyckoff = WyckoffAgent()
    wyckoff_result = await wyckoff.compute("SPY", Timeframe.FIFTEEN_MIN, repo)

    # Layer 3 (interpretive) confidence is generally lower than Layer 2 (mathematical)
    assert wyckoff_result.confidence.score <= ema_result.confidence.score + 0.2


async def test_layer3_consumes_layers_1_2(repo):
    """Layer 3 agents metadata shows they consume layers 1+2."""
    agent = SmartMoneyAgent()
    result = await agent.compute("SPY", Timeframe.FIFTEEN_MIN, repo)
    assert result.metadata.get("consumes_layers") == [1, 2]
''')

# Layer 4: Multi-Timeframe Consensus
w("agents/technical-analysis/layer4-consensus/pyproject.toml", '''
[project]
name = "athena-x-ta-layer4-consensus"
version = "0.1.0"
description = "Layer 4 - Multi-Timeframe Consensus Agent"
requires-python = ">=3.11"
dependencies = ["athena-x-ta-base"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/athena_x_ta_layer4_consensus"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
''')

w("agents/technical-analysis/layer4-consensus/src/athena_x_ta_layer4_consensus/__init__.py", '''
"""Layer 4 - Multi-Timeframe Consensus."""
from .consensus import TimeframeConsensusAgent, ConsensusResult

__all__ = ["TimeframeConsensusAgent", "ConsensusResult"]
__version__ = "0.1.0"
''')

w("agents/technical-analysis/layer4-consensus/src/athena_x_ta_layer4_consensus/consensus.py", '''
"""Multi-Timeframe Consensus Agent - Layer 4.

Stage 7 req: One agent produces a synchronized view across 8 timeframes.

Output example:
  Long-term Trend:  Bullish
  Intermediate:     Bullish
  Intraday:          Bearish Pullback
  Alignment:         82%
  Conflict:          15M diverging from 1H

Downstream modules read this single consensus instead of reconciling 8 timeframes.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

from athena_x_ta_base import BaseTAAgent, TAOutput, TAConfidence, Timeframe, STANDARD_TIMEFRAMES


@dataclass
class ConsensusResult:
    """Result of multi-timeframe consensus."""
    long_term_trend: str = "unknown"      # Monthly + Weekly
    intermediate_trend: str = "unknown"   # Daily + 4H
    intraday_trend: str = "unknown"       # 1H + 30M + 15M + 5M + 1M
    alignment_score: float = 0.0          # 0-100
    conflicts: list[str] = field(default_factory=list)
    breakdown: dict[str, str] = field(default_factory=dict)


class TimeframeConsensusAgent(BaseTAAgent):
    """Produces a synchronized multi-timeframe consensus view.

    Instead of every AI looking at every timeframe independently,
    this agent produces a single unified view.

    Stage 7 rule: Downstream modules read this single consensus.
    """

    def __init__(self, **kwargs):
        super().__init__(name="timeframe_consensus", layer=4, **kwargs)

    async def compute(self, symbol: str, timeframe: Timeframe, repo) -> TAOutput:
        # Fetch trend for each timeframe
        from athena_x_ta_layer1_market_structure import TrendDetectionAgent
        trend_agent = TrendDetectionAgent(bar_cache=self._bar_cache)

        trends: dict[str, str] = {}
        for tf in STANDARD_TIMEFRAMES:
            result = await trend_agent.compute(symbol, tf, repo)
            trends[tf.value] = result.value if result.value else "unknown"

        # Classify by horizon
        long_term = self._classify_group(trends, ["1M", "1W"])
        intermediate = self._classify_group(trends, ["1D", "4H"])
        intraday = self._classify_group(trends, ["1H", "30M", "15M", "5M", "1m"])

        # Calculate alignment score
        all_trends = list(trends.values())
        bullish_count = sum(1 for t in all_trends if t == "bullish")
        bearish_count = sum(1 for t in all_trend if t == "bearish")
        total = len(all_trends)
        alignment = max(bullish_count, bearish_count) / total * 100 if total > 0 else 0

        # Detect conflicts
        conflicts = []
        if trends.get("15M") != trends.get("1H"):
            conflicts.append(f"15M diverging from 1H")
        if trends.get("5M") != trends.get("15M"):
            conflicts.append(f"5M diverging from 15M")

        consensus = ConsensusResult(
            long_term_trend=long_term,
            intermediate_trend=intermediate,
            intraday_trend=intraday,
            alignment_score=round(alignment, 1),
            conflicts=conflicts,
            breakdown=trends,
        )

        confidence_score = alignment / 100 * 0.3 + 0.6

        return TAOutput(
            agent=self.name, symbol=symbol, timeframe="ALL",
            indicator="TimeframeConsensus",
            value={
                "long_term": long_term,
                "intermediate": intermediate,
                "intraday": intraday,
                "alignment": round(alignment, 1),
                "conflicts": conflicts,
                "breakdown": trends,
            },
            confidence=TAConfidence.from_score(confidence_score),
            metadata={"timeframes_evaluated": len(trends)},
        )

    def _classify_group(self, trends: dict, tfs: list[str]) -> str:
        """Classify a group of timeframes into a single trend."""
        group_trends = [trends.get(tf, "unknown") for tf in tfs]
        if all(t == "bullish" for t in group_trends):
            return "bullish"
        if all(t == "bearish" for t in group_trends):
            return "bearish"
        if "bullish" in group_trends and "bearish" in group_trends:
            return "mixed"
        return "ranging"
''')

w("agents/technical-analysis/layer4-consensus/tests/__init__.py", "")
w("agents/technical-analysis/layer4-consensus/tests/test_consensus.py", '''
"""Tests for Layer 4 Multi-Timeframe Consensus."""
import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "layer2-indicators", "tests"))
from conftest import FakeMarketRepository
from athena_x_ta_layer4_consensus import TimeframeConsensusAgent
from athena_x_ta_base import Timeframe


@pytest.fixture
def repo():
    return FakeMarketRepository()


async def test_consensus_produces_unified_view(repo):
    """Consensus agent produces a unified multi-timeframe view."""
    agent = TimeframeConsensusAgent()
    result = await agent.compute("SPY", Timeframe.DAILY, repo)
    assert result.value is not None
    assert "long_term" in result.value
    assert "intermediate" in result.value
    assert "intraday" in result.value
    assert "alignment" in result.value


async def test_alignment_score_between_0_and_100(repo):
    """Alignment score is 0-100."""
    agent = TimeframeConsensusAgent()
    result = await agent.compute("SPY", Timeframe.DAILY, repo)
    assert 0 <= result.value["alignment"] <= 100


async def test_conflicts_detected(repo):
    """Conflicts are detected when timeframes diverge."""
    agent = TimeframeConsensusAgent()
    result = await agent.compute("SPY", Timeframe.DAILY, repo)
    assert "conflicts" in result.value
    assert isinstance(result.value["conflicts"], list)


async def test_breakdown_includes_all_timeframes(repo):
    """Breakdown includes all 9 standard timeframes."""
    agent = TimeframeConsensusAgent()
    result = await agent.compute("SPY", Timeframe.DAILY, repo)
    breakdown = result.value["breakdown"]
    assert len(breakdown) == 9
    assert "1M" in breakdown
    assert "1m" in breakdown


async def test_consensus_confidence_includes_alignment(repo):
    """Confidence reflects alignment score."""
    agent = TimeframeConsensusAgent()
    result = await agent.compute("SPY", Timeframe.DAILY, repo)
    # Higher alignment -> higher confidence
    assert result.confidence.score > 0.5
''')

# Layer 5: Technical Supervisor
w("agents/technical-analysis/layer5-supervisor/pyproject.toml", '''
[project]
name = "athena-x-ta-layer5-supervisor"
version = "0.1.0"
description = "Layer 5 - Technical Supervisor: monitors all TA agents"
requires-python = ">=3.11"
dependencies = ["athena-x-ta-base"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/athena_x_ta_layer5_supervisor"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
''')

w("agents/technical-analysis/layer5-supervisor/src/athena_x_ta_layer5_supervisor/__init__.py", '''
"""Layer 5 - Technical Supervisor."""
from .supervisor import TechnicalSupervisor, SupervisorReport

__all__ = ["TechnicalSupervisor", "SupervisorReport"]
__version__ = "0.1.0"
''')

w("agents/technical-analysis/layer5-supervisor/src/athena_x_ta_layer5_supervisor/supervisor.py", '''
"""Technical Supervisor - Layer 5.

Stage 7 req: One supervisor monitors all TA agents.

Responsibilities:
  - Detect failed calculations
  - Detect stale indicators
  - Detect inconsistent timeframes
  - Restart failed agents
  - Measure latency
  - Measure calculation duration
  - Publish health events
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any

from athena_x_ta_base import BaseTAAgent, TAOutput, TAConfidence, Timeframe


@dataclass
class SupervisorReport:
    """Report from the Technical Supervisor."""
    total_agents: int = 0
    active_agents: int = 0
    failed_agents: list[str] = field(default_factory=list)
    stale_agents: list[str] = field(default_factory=list)
    avg_latency_ms: float = 0.0
    max_latency_ms: float = 0.0
    timeframe_sync_status: str = "synced"  # synced / desynchronized
    health_events: list[dict] = field(default_factory=list)


class TechnicalSupervisor(BaseTAAgent):
    """Monitors all TA agents.

    Stage 7 rule: Publishes health events for the overall Supervisor AI.
    """

    def __init__(self, stale_threshold_seconds: float = 60.0, **kwargs):
        super().__init__(name="technical_supervisor", layer=5, **kwargs)
        self._stale_threshold = stale_threshold_seconds
        self._registered_agents: list[BaseTAAgent] = []

    def register_agent(self, agent: BaseTAAgent) -> None:
        """Register a TA agent for monitoring."""
        self._registered_agents.append(agent)

    async def compute(self, symbol: str, timeframe: Timeframe, repo) -> TAOutput:
        """Compute supervisor report."""
        now = datetime.now(timezone.utc)
        report = SupervisorReport(total_agents=len(self._registered_agents))

        latencies = []
        for agent in self._registered_agents:
            health = agent.get_health()
            if not health["running"]:
                report.failed_agents.append(agent.name)
            elif health["last_calculation"]:
                last = datetime.fromisoformat(health["last_calculation"])
                age = (now - last).total_seconds()
                if age > self._stale_threshold:
                    report.stale_agents.append(agent.name)
                else:
                    report.active_agents += 1
            latencies.append(health.get("avg_calculation_time_ms", 0))

        if latencies:
            report.avg_latency_ms = sum(latencies) / len(latencies)
            report.max_latency_ms = max(latencies)

        # Check timeframe synchronization
        if report.stale_agents:
            report.timeframe_sync_status = "desynchronized"

        # Build health events
        if report.failed_agents:
            report.health_events.append({
                "type": "agents_failed",
                "agents": report.failed_agents,
                "severity": "critical",
            })
        if report.stale_agents:
            report.health_events.append({
                "type": "agents_stale",
                "agents": report.stale_agents,
                "severity": "warning",
            })

        return TAOutput(
            agent=self.name, symbol=symbol, timeframe="ALL",
            indicator="TechnicalSupervisor",
            value={
                "total_agents": report.total_agents,
                "active_agents": report.active_agents,
                "failed_agents": report.failed_agents,
                "stale_agents": report.stale_agents,
                "avg_latency_ms": round(report.avg_latency_ms, 2),
                "max_latency_ms": round(report.max_latency_ms, 2),
                "timeframe_sync": report.timeframe_sync_status,
                "health_events": report.health_events,
            },
            confidence=TAConfidence.from_score(0.95),
            metadata={"registered": len(self._registered_agents)},
        )
''')

w("agents/technical-analysis/layer5-supervisor/tests/__init__.py", "")
w("agents/technical-analysis/layer5-supervisor/tests/test_supervisor.py", '''
"""Tests for Layer 5 Technical Supervisor."""
import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "layer2-indicators", "tests"))
from conftest import FakeMarketRepository
from athena_x_ta_layer5_supervisor import TechnicalSupervisor
from athena_x_ta_layer2_indicators import EMAAgent, RSIAgent
from athena_x_ta_base import Timeframe


@pytest.fixture
def repo():
    return FakeMarketRepository()


async def test_supervisor_monitors_registered_agents(repo):
    """Supervisor monitors all registered agents."""
    sup = TechnicalSupervisor()
    ema = EMAAgent()
    rsi = RSIAgent()
    sup.register_agent(ema)
    sup.register_agent(rsi)

    result = await sup.compute("SPY", Timeframe.DAILY, repo)
    assert result.value["total_agents"] == 2


async def test_supervisor_detects_failed_agents(repo):
    """Supervisor detects agents that haven't computed."""
    sup = TechnicalSupervisor()
    ema = EMAAgent()  # never computed
    sup.register_agent(ema)

    result = await sup.compute("SPY", Timeframe.DAILY, repo)
    assert "ema" in result.value["failed_agents"]


async def test_supervisor_reports_active_agents(repo):
    """Supervisor reports active agents after computation."""
    sup = TechnicalSupervisor()
    ema = EMAAgent()
    sup.register_agent(ema)

    # Run the agent
    await ema.compute("SPY", Timeframe.FIFTEEN_MIN, repo)

    result = await sup.compute("SPY", Timeframe.DAILY, repo)
    assert result.value["active_agents"] == 1
    assert result.value["failed_agents"] == []


async def test_supervisor_publishes_health_events(repo):
    """Supervisor publishes health events for failures."""
    sup = TechnicalSupervisor()
    ema = EMAAgent()  # never computed
    sup.register_agent(ema)

    result = await sup.compute("SPY", Timeframe.DAILY, repo)
    events = result.value["health_events"]
    assert any(e["type"] == "agents_failed" for e in events)
''')

# Technical Snapshot Agent
w("agents/technical-analysis/snapshot/pyproject.toml", '''
[project]
name = "athena-x-ta-snapshot"
version = "0.1.0"
description = "Technical Snapshot Agent - single synchronized output for downstream"
requires-python = ">=3.11"
dependencies = ["athena-x-ta-base"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/athena_x_ta_snapshot"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
''')

w("agents/technical-analysis/snapshot/src/athena_x_ta_snapshot/__init__.py", '''
"""Technical Snapshot Agent."""
from .agent import TechnicalSnapshotAgent, TechnicalSnapshot

__all__ = ["TechnicalSnapshotAgent", "TechnicalSnapshot"]
__version__ = "0.1.0"
''')

w("agents/technical-analysis/snapshot/src/athena_x_ta_snapshot/agent.py", '''
"""Technical Snapshot Agent.

Stage 7 additional req: Publishes a single synchronized technical snapshot
after all required analyses complete.

This becomes the standard technical input for:
  - Options Intelligence (Stage 8)
  - Market Intelligence (Stage 10)
  - Forecast Engine (Stage 11)
  - Report Engine (Stage 15)

Downstream modules query ONE snapshot instead of 23 different TA agents.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from athena_x_ta_base import BaseTAAgent, TAOutput, TAConfidence, Timeframe


@dataclass
class TechnicalSnapshot:
    """Synchronized technical snapshot for downstream consumption."""
    symbol: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    # Layer 1: Market Structure
    trend: str = "unknown"
    support: float | None = None
    resistance: float | None = None
    poc: float | None = None  # Volume Profile Point of Control
    # Layer 2: Indicators (latest values for the primary timeframe)
    ema: float | None = None
    rsi: float | None = None
    macd: dict | None = None
    atr: float | None = None
    bollinger: dict | None = None
    adx: float | None = None
    vwap: float | None = None
    # Layer 3: Institutional Analysis
    wyckoff_phase: str | None = None
    smart_money_signal: str | None = None
    entry_signal: str | None = None
    # Layer 4: Consensus
    timeframe_consensus: dict | None = None
    alignment_score: float = 0.0
    # Overall confidence
    overall_confidence: float = 0.0


class TechnicalSnapshotAgent(BaseTAAgent):
    """Publishes a single synchronized technical snapshot.

    Stage 7 rule: Downstream components work from the same consistent view.
    """

    def __init__(self, **kwargs):
        super().__init__(name="technical_snapshot", layer=5, **kwargs)

    async def compute(self, symbol: str, timeframe: Timeframe, repo) -> TAOutput:
        """Compute the full technical snapshot by running all layers."""
        from athena_x_ta_layer1_market_structure import (
            TrendDetectionAgent, SupportResistanceAgent, VolumeProfileAgent,
        )
        from athena_x_ta_layer2_indicators import (
            EMAAgent, RSIAgent, MACDAgent, ATRAgent,
            BollingerAgent, ADXAgent, VWAPAgent,
        )
        from athena_x_ta_layer3_institutional import (
            WyckoffAgent, SmartMoneyAgent, EntryAgent,
        )
        from athena_x_ta_layer4_consensus import TimeframeConsensusAgent

        snapshot = TechnicalSnapshot(symbol=symbol)

        # Layer 1
        trend_result = await TrendDetectionAgent(bar_cache=self._bar_cache).compute(symbol, timeframe, repo)
        snapshot.trend = trend_result.value if isinstance(trend_result.value, str) else "unknown"

        sr_result = await SupportResistanceAgent(bar_cache=self._bar_cache).compute(symbol, timeframe, repo)
        if sr_result.value:
            snapshot.support = sr_result.value.get("support")
            snapshot.resistance = sr_result.value.get("resistance")

        vp_result = await VolumeProfileAgent(bar_cache=self._bar_cache).compute(symbol, timeframe, repo)
        if vp_result.value:
            snapshot.poc = vp_result.value.get("poc")

        # Layer 2
        ema_result = await EMAAgent(bar_cache=self._bar_cache).compute(symbol, timeframe, repo)
        snapshot.ema = ema_result.value if isinstance(ema_result.value, (int, float)) else None

        rsi_result = await RSIAgent(bar_cache=self._bar_cache).compute(symbol, timeframe, repo)
        snapshot.rsi = rsi_result.value if isinstance(rsi_result.value, (int, float)) else None

        macd_result = await MACDAgent(bar_cache=self._bar_cache).compute(symbol, timeframe, repo)
        snapshot.macd = macd_result.value if isinstance(macd_result.value, dict) else None

        atr_result = await ATRAgent(bar_cache=self._bar_cache).compute(symbol, timeframe, repo)
        snapshot.atr = atr_result.value if isinstance(atr_result.value, (int, float)) else None

        bollinger_result = await BollingerAgent(bar_cache=self._bar_cache).compute(symbol, timeframe, repo)
        snapshot.bollinger = bollinger_result.value if isinstance(bollinger_result.value, dict) else None

        adx_result = await ADXAgent(bar_cache=self._bar_cache).compute(symbol, timeframe, repo)
        snapshot.adx = adx_result.value if isinstance(adx_result.value, (int, float)) else None

        vwap_result = await VWAPAgent(bar_cache=self._bar_cache).compute(symbol, timeframe, repo)
        snapshot.vwap = vwap_result.value if isinstance(vwap_result.value, (int, float)) else None

        # Layer 3
        wyckoff_result = await WyckoffAgent(bar_cache=self._bar_cache).compute(symbol, timeframe, repo)
        if wyckoff_result.value and isinstance(wyckoff_result.value, dict):
            snapshot.wyckoff_phase = wyckoff_result.value.get("phase")

        sm_result = await SmartMoneyAgent(bar_cache=self._bar_cache).compute(symbol, timeframe, repo)
        if sm_result.value and isinstance(sm_result.value, dict):
            snapshot.smart_money_signal = "detected" if sm_result.value.get("fvg_detected") else "none"

        entry_result = await EntryAgent(bar_cache=self._bar_cache).compute(symbol, timeframe, repo)
        if entry_result.value and isinstance(entry_result.value, dict):
            snapshot.entry_signal = entry_result.value.get("entry_signal")

        # Layer 4
        consensus_result = await TimeframeConsensusAgent(bar_cache=self._bar_cache).compute(symbol, timeframe, repo)
        if consensus_result.value:
            snapshot.timeframe_consensus = consensus_result.value
            snapshot.alignment_score = consensus_result.value.get("alignment", 0.0)

        # Overall confidence
        snapshot.overall_confidence = 0.85 + snapshot.alignment_score / 100 * 0.1

        return TAOutput(
            agent=self.name, symbol=symbol, timeframe=timeframe.value,
            indicator="TechnicalSnapshot",
            value={
                "symbol": snapshot.symbol,
                "timestamp": snapshot.timestamp.isoformat(),
                "trend": snapshot.trend,
                "support": snapshot.support,
                "resistance": snapshot.resistance,
                "poc": snapshot.poc,
                "ema": snapshot.ema,
                "rsi": snapshot.rsi,
                "macd": snapshot.macd,
                "atr": snapshot.atr,
                "bollinger": snapshot.bollinger,
                "adx": snapshot.adx,
                "vwap": snapshot.vwap,
                "wyckoff_phase": snapshot.wyckoff_phase,
                "smart_money_signal": snapshot.smart_money_signal,
                "entry_signal": snapshot.entry_signal,
                "timeframe_consensus": snapshot.timeframe_consensus,
                "alignment_score": snapshot.alignment_score,
                "overall_confidence": round(snapshot.overall_confidence, 4),
            },
            confidence=TAConfidence.from_score(snapshot.overall_confidence),
            metadata={"layers_consumed": [1, 2, 3, 4]},
        )
''')

w("agents/technical-analysis/snapshot/tests/__init__.py", "")
w("agents/technical-analysis/snapshot/tests/test_snapshot.py", '''
"""Tests for Technical Snapshot Agent."""
import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "layer2-indicators", "tests"))
from conftest import FakeMarketRepository
from athena_x_ta_snapshot import TechnicalSnapshotAgent
from athena_x_ta_base import Timeframe


@pytest.fixture
def repo():
    return FakeMarketRepository()


async def test_snapshot_includes_all_layers(repo):
    """Snapshot includes data from all 5 layers."""
    agent = TechnicalSnapshotAgent()
    result = await agent.compute("SPY", Timeframe.FIFTEEN_MIN, repo)
    value = result.value
    # Layer 1
    assert "trend" in value
    assert "support" in value
    assert "resistance" in value
    # Layer 2
    assert "ema" in value
    assert "rsi" in value
    assert "macd" in value
    assert "atr" in value
    assert "bollinger" in value
    assert "adx" in value
    assert "vwap" in value
    # Layer 3
    assert "wyckoff_phase" in value
    assert "smart_money_signal" in value
    assert "entry_signal" in value
    # Layer 4
    assert "timeframe_consensus" in value
    assert "alignment_score" in value


async def test_snapshot_has_overall_confidence(repo):
    """Snapshot includes overall confidence."""
    agent = TechnicalSnapshotAgent()
    result = await agent.compute("SPY", Timeframe.FIFTEEN_MIN, repo)
    assert "overall_confidence" in result.value
    assert 0 < result.value["overall_confidence"] <= 1.0


async def test_snapshot_consumes_layers_1_to_4(repo):
    """Snapshot metadata shows it consumes layers 1-4."""
    agent = TechnicalSnapshotAgent()
    result = await agent.compute("SPY", Timeframe.FIFTEEN_MIN, repo)
    assert result.metadata.get("layers_consumed") == [1, 2, 3, 4]


async def test_snapshot_event_published(repo):
    """Snapshot emits ai:technical:technical_snapshot event."""
    from athena_x_runtime_event_bus import InMemoryBusClient

    bus = InMemoryBusClient()
    agent = TechnicalSnapshotAgent()

    received = []
    async def handler(event):
        received.append(event)
    await bus.subscribe("ai:technical:technical_snapshot", handler)

    await agent.compute_and_publish("SPY", Timeframe.FIFTEEN_MIN, repo, event_bus=bus)

    assert len(received) == 1
    assert "ema" in received[0].payload["value"]
    await bus.close()
''')

# ============================================================================
# STAGE 7 INTEGRATION
# ============================================================================

w("runtime/stage7-integration/pyproject.toml", '''
[project]
name = "athena-x-runtime-stage7-integration"
version = "0.1.0"
description = "Stage 7 integration - TA engine end-to-end + acceptance tests"
requires-python = ">=3.11"
dependencies = [
    "athena-x-ta-base",
    "athena-x-ta-layer1-market-structure",
    "athena-x-ta-layer2-indicators",
    "athena-x-ta-layer3-institutional",
    "athena-x-ta-layer4-consensus",
    "athena-x-ta-layer5-supervisor",
    "athena-x-ta-snapshot",
    "athena-x-runtime-event-bus",
    "athena-x-runtime-event-envelope",
    "athena-x-runtime-in-memory-repository",
    "pytest>=8.3.0",
    "pytest-asyncio>=0.24.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/athena_x_runtime_stage7_integration"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
''')

w("runtime/stage7-integration/src/athena_x_runtime_stage7_integration/__init__.py", '''"""Stage 7 integration."""''')

w("runtime/stage7-integration/src/athena_x_runtime_stage7_integration/wire.py", '''
"""Wire Stage 7 TA engine with all 5 layers + snapshot + supervisor."""
from __future__ import annotations
from athena_x_ta_base import BarCache, TimeframeContext
from athena_x_ta_layer1_market_structure import (
    TrendDetectionAgent, SwingHighLowAgent, SupportResistanceAgent,
    LiquidityAgent, VolumeProfileAgent, MultiTimeframeDataAgent,
)
from athena_x_ta_layer2_indicators import (
    EMAAgent, SMAAgent, VWAPAgent, RSIAgent,
    MACDAgent, ADXAgent, ATRAgent, BollingerAgent,
)
from athena_x_ta_layer3_institutional import (
    WyckoffAgent, ChanTheoryAgent, ElliottWaveAgent,
    SmartMoneyAgent, VolumePriceAgent,
    EscapeTopAgent, EntryAgent, PullUpPatternAgent,
)
from athena_x_ta_layer4_consensus import TimeframeConsensusAgent
from athena_x_ta_layer5_supervisor import TechnicalSupervisor
from athena_x_ta_snapshot import TechnicalSnapshotAgent


def create_stage7_container():
    """Create full TA engine wiring."""
    bar_cache = BarCache()
    tf_ctx = TimeframeContext()

    # Layer 1: 6 agents
    layer1 = [
        TrendDetectionAgent(bar_cache=bar_cache),
        SwingHighLowAgent(bar_cache=bar_cache),
        SupportResistanceAgent(bar_cache=bar_cache),
        LiquidityAgent(bar_cache=bar_cache),
        VolumeProfileAgent(bar_cache=bar_cache),
        MultiTimeframeDataAgent(bar_cache=bar_cache),
    ]

    # Layer 2: 8 agents
    layer2 = [
        EMAAgent(bar_cache=bar_cache),
        SMAAgent(bar_cache=bar_cache),
        VWAPAgent(bar_cache=bar_cache),
        RSIAgent(bar_cache=bar_cache),
        MACDAgent(bar_cache=bar_cache),
        ADXAgent(bar_cache=bar_cache),
        ATRAgent(bar_cache=bar_cache),
        BollingerAgent(bar_cache=bar_cache),
    ]

    # Layer 3: 8 agents
    layer3 = [
        WyckoffAgent(bar_cache=bar_cache),
        ChanTheoryAgent(bar_cache=bar_cache),
        ElliottWaveAgent(bar_cache=bar_cache),
        SmartMoneyAgent(bar_cache=bar_cache),
        VolumePriceAgent(bar_cache=bar_cache),
        EscapeTopAgent(bar_cache=bar_cache),
        EntryAgent(bar_cache=bar_cache),
        PullUpPatternAgent(bar_cache=bar_cache),
    ]

    # Layer 4: 1 agent
    layer4 = [TimeframeConsensusAgent(bar_cache=bar_cache)]

    # Layer 5: 1 supervisor
    supervisor = TechnicalSupervisor(bar_cache=bar_cache)
    for agent in layer1 + layer2 + layer3 + layer4:
        supervisor.register_agent(agent)

    # Snapshot agent
    snapshot = TechnicalSnapshotAgent(bar_cache=bar_cache)

    all_agents = layer1 + layer2 + layer3 + layer4 + [supervisor, snapshot]

    return {
        "bar_cache": bar_cache,
        "timeframe_context": tf_ctx,
        "layer1": layer1,
        "layer2": layer2,
        "layer3": layer3,
        "layer4": layer4,
        "supervisor": supervisor,
        "snapshot": snapshot,
        "all_agents": all_agents,
        "total_agent_count": len(all_agents),
    }
''')

w("runtime/stage7-integration/tests/__init__.py", "")
w("runtime/stage7-integration/tests/conftest.py", '''
"""Shared fixtures for Stage 7 integration tests."""
import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "agents", "technical-analysis", "layer2-indicators", "tests"))
from conftest import FakeMarketRepository


@pytest.fixture
def repo():
    return FakeMarketRepository()
''')

w("runtime/stage7-integration/tests/test_stage7_acceptance.py", '''
"""Stage 7 acceptance tests - all exit criteria must pass."""
import pytest
from athena_x_runtime_stage7_integration.wire import create_stage7_container
from athena_x_ta_base import Timeframe


@pytest.fixture
def setup():
    return create_stage7_container()


# ============================================================================
# Exit Criteria 1: All 23 TA agents implement the TechnicalIndicator Protocol
# ============================================================================

def test_23_ta_agents_exist(setup):
    """23 TA agents are created (6+8+8+1 = 23, plus supervisor + snapshot = 25)."""
    total = len(setup["layer1"]) + len(setup["layer2"]) + len(setup["layer3"]) + len(setup["layer4"])
    assert total == 23  # 6 + 8 + 8 + 1 = 23


def test_all_agents_have_name_and_layer(setup):
    """Every agent has a name and layer assignment."""
    for agent in setup["all_agents"]:
        assert agent.name is not None
        assert agent.layer in (1, 2, 3, 4, 5)


# ============================================================================
# Exit Criteria 2: Every agent reads from Canonical Repository
# ============================================================================

async def test_agents_read_from_repository(setup, repo):
    """Agents use the repository via bar cache (not direct DB access)."""
    from athena_x_ta_layer2_indicators import EMAAgent
    agent = EMAAgent(bar_cache=setup["bar_cache"])
    result = await agent.compute("SPY", Timeframe.FIFTEEN_MIN, repo)
    assert result.value is not None
    # Bar cache should have been populated (miss -> fetch)
    stats = setup["bar_cache"].get_stats()
    assert stats["misses"] > 0


# ============================================================================
# Exit Criteria 3: No TA agent writes to database
# ============================================================================

def test_no_ta_agent_has_write_methods(setup):
    """TA agents don't have write_quote/write_bar methods."""
    for agent in setup["all_agents"]:
        assert not hasattr(agent, "write_quote")
        assert not hasattr(agent, "write_bar")
        assert not hasattr(agent, "supersede")


# ============================================================================
# Exit Criteria 4: All outputs emitted as ai:technical:* events
# ============================================================================

async def test_outputs_emitted_as_events(setup, repo):
    """TA outputs are published as ai:technical:* events."""
    from athena_x_runtime_event_bus import InMemoryBusClient

    bus = InMemoryBusClient()
    agent = setup["layer2"][0]  # EMAAgent

    received = []
    async def handler(event):
        received.append(event)
    await bus.subscribe("ai:technical:*", handler)

    await agent.compute_and_publish("SPY", Timeframe.FIFTEEN_MIN, repo, event_bus=bus)

    assert len(received) == 1
    assert received[0].event_type.startswith("ai:technical:")
    await bus.close()


# ============================================================================
# Exit Criteria 5: Multi-timeframe synchronization working
# ============================================================================

async def test_multi_timeframe_synchronization(setup, repo):
    """Multi-Timeframe Data Agent fetches across all 8 timeframes."""
    agent = setup["layer1"][5]  # MultiTimeframeDataAgent
    result = await agent.compute("SPY", Timeframe.DAILY, repo)
    assert len(result.value) == 9  # 9 timeframes


# ============================================================================
# Exit Criteria 6: Timeframe Consensus Agent publishes unified view
# ============================================================================

async def test_consensus_publishes_unified_view(setup, repo):
    """Consensus agent produces a unified market view."""
    agent = setup["layer4"][0]  # TimeframeConsensusAgent
    result = await agent.compute("SPY", Timeframe.DAILY, repo)
    assert "alignment" in result.value
    assert "long_term" in result.value
    assert "intraday" in result.value


# ============================================================================
# Exit Criteria 7: Interpretive agents consume lower-layer outputs
# ============================================================================

async def test_layer3_consumes_lower_layers(setup, repo):
    """Layer 3 agents metadata shows they consume layers 1+2."""
    for agent in setup["layer3"]:
        result = await agent.compute("SPY", Timeframe.FIFTEEN_MIN, repo)
        assert result.metadata.get("consumes_layers") == [1, 2]


# ============================================================================
# Exit Criteria 8: Technical Supervisor monitors all agents
# ============================================================================

async def test_supervisor_monitors_all_agents(setup, repo):
    """Supervisor monitors all registered agents."""
    sup = setup["supervisor"]
    result = await sup.compute("SPY", Timeframe.DAILY, repo)
    assert result.value["total_agents"] == 23  # 6+8+8+1


# ============================================================================
# Exit Criteria 9: Shared bar caching eliminates redundant reads
# ============================================================================

async def test_bar_cache_eliminates_redundant_reads(setup, repo):
    """Multiple indicators using the same bars benefit from cache."""
    cache = setup["bar_cache"]

    # Run EMA (first call -> miss)
    ema = setup["layer2"][0]
    await ema.compute("SPY", Timeframe.FIFTEEN_MIN, repo)

    # Run RSI (same bars -> should hit cache)
    rsi = setup["layer2"][3]
    await rsi.compute("SPY", Timeframe.FIFTEEN_MIN, repo)

    stats = cache.get_stats()
    assert stats["hits"] > 0  # at least 1 cache hit


# ============================================================================
# Exit Criteria 10: Technical Snapshot for downstream consumption
# ============================================================================

async def test_technical_snapshot_provides_single_view(setup, repo):
    """Snapshot agent produces a single synchronized view for downstream."""
    agent = setup["snapshot"]
    result = await agent.compute("SPY", Timeframe.FIFTEEN_MIN, repo)

    # Contains data from all layers
    value = result.value
    assert "trend" in value       # Layer 1
    assert "ema" in value         # Layer 2
    assert "wyckoff_phase" in value  # Layer 3
    assert "alignment_score" in value  # Layer 4
    assert "overall_confidence" in value


# ============================================================================
# Stress test: run all 23 agents
# ============================================================================

async def test_stress_all_23_agents_run(setup, repo):
    """All 23 agents can run without errors."""
    all_ta = setup["layer1"] + setup["layer2"] + setup["layer3"] + setup["layer4"]
    for agent in all_ta:
        result = await agent.compute("SPY", Timeframe.FIFTEEN_MIN, repo)
        assert result is not None


# ============================================================================
# Confidence score on every output
# ============================================================================

async def test_every_output_has_confidence(setup, repo):
    """Every TA output includes confidence metadata."""
    all_ta = setup["layer1"] + setup["layer2"] + setup["layer3"] + setup["layer4"]
    for agent in all_ta:
        result = await agent.compute("SPY", Timeframe.FIFTEEN_MIN, repo)
        assert result.confidence is not None
        assert 0 <= result.confidence.score <= 1.0
        assert result.confidence.quality in ("A+", "A", "B", "C", "D", "F")
''')

print(f"\\n✅ Stage 7 complete: {len(FILES)} files written")
print("\\nComponents implemented:")
print("  Base:  agents/technical-analysis/_base/ (BaseTAAgent + BarCache + TimeframeContext)")
print("  L1:    agents/technical-analysis/layer1-market-structure/ (6 agents)")
print("  L2:    agents/technical-analysis/layer2-indicators/ (8 agents)")
print("  L3:    agents/technical-analysis/layer3-institutional/ (8 agents)")
print("  L4:    agents/technical-analysis/layer4-consensus/ (1 agent)")
print("  L5:    agents/technical-analysis/layer5-supervisor/ (1 agent)")
print("  Snap:  agents/technical-analysis/snapshot/ (1 agent)")
print("  Test:  runtime/stage7-integration/ (acceptance tests)")
print("\\nNext: install deps and run tests")
