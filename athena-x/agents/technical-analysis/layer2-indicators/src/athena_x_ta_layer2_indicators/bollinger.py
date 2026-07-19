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
