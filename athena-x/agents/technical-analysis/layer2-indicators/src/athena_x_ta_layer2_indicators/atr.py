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
