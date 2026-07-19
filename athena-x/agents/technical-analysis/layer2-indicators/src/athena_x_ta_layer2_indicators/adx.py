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
