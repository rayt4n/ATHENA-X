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
