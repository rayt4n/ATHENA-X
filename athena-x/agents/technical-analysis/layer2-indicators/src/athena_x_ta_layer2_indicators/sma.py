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
