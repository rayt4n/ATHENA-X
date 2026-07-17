"""Multi-Timeframe Data Agent - Layer 1.

Fetches + synchronizes OHLCV across 8 timeframes.
"""
from __future__ import annotations
from athena_x_ta_base import BaseTAAgent, TAOutput, TAConfidence, Timeframe, STANDARD_TIMEFRAMES


class MultiTimeframeDataAgent(BaseTAAgent):
    """Fetches bars across all standard timeframes."""

    def __init__(self, **kwargs):
        super().__init__(name="multi_timeframe_data", layer=1, **kwargs)

    async def compute(self, symbol: str, timeframe: Timeframe, repo) -> TAOutput:
        results = {}
        for tf in STANDARD_TIMEFRAMES:
            bars = await self._bar_cache.get_bars(repo, symbol, tf.value, count=50)
            results[tf.value] = {
                "bar_count": len(bars.bars),
                "latest_close": bars.closes[-1] if bars.closes else None,
            }

        return TAOutput(
            agent=self.name, symbol=symbol, timeframe="ALL",
            indicator="MultiTimeframeData",
            value=results,
            confidence=TAConfidence.from_score(0.95),
            metadata={"timeframes": len(results)},
        )
