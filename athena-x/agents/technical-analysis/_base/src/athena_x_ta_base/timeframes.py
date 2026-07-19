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
