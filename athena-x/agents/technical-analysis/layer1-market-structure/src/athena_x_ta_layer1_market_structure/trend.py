"""Trend Detection Agent - Layer 1."""
from __future__ import annotations
from athena_x_ta_base import BaseTAAgent, TAOutput, TAConfidence, Timeframe


class TrendDetectionAgent(BaseTAAgent):
    """Detects trend direction: Bullish / Bearish / Ranging."""

    def __init__(self, **kwargs):
        super().__init__(name="trend", layer=1, **kwargs)

    async def compute(self, symbol: str, timeframe: Timeframe, repo) -> TAOutput:
        bars = await self._bar_cache.get_bars(repo, symbol, timeframe.value, count=50)
        closes = bars.closes

        if len(closes) < 20:
            return TAOutput(
                agent=self.name, symbol=symbol, timeframe=timeframe.value,
                indicator="Trend", value="unknown",
                confidence=TAConfidence.from_score(0.3),
            )

        # Simple trend detection: compare recent closes to older closes
        recent_avg = sum(closes[-10:]) / 10
        older_avg = sum(closes[-20:-10]) / 10
        change_pct = (recent_avg - older_avg) / older_avg if older_avg > 0 else 0

        if change_pct > 0.002:
            trend = "bullish"
            confidence = 0.85 + min(0.1, abs(change_pct) * 10)
        elif change_pct < -0.002:
            trend = "bearish"
            confidence = 0.85 + min(0.1, abs(change_pct) * 10)
        else:
            trend = "ranging"
            confidence = 0.75

        return TAOutput(
            agent=self.name, symbol=symbol, timeframe=timeframe.value,
            indicator="Trend", value=trend,
            confidence=TAConfidence.from_score(confidence),
            metadata={"change_pct": round(change_pct * 100, 4)},
        )
