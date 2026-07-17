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
