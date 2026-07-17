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
