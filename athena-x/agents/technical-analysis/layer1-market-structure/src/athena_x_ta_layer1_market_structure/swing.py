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
