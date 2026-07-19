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
