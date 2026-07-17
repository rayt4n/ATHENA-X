"""VWAP Agent - Volume-Weighted Average Price (Layer 2)."""
from __future__ import annotations
from athena_x_ta_base import BaseTAAgent, TAOutput, TAConfidence, Timeframe


class VWAPAgent(BaseTAAgent):
    def __init__(self, **kwargs):
        super().__init__(name="vwap", layer=2, **kwargs)

    async def compute(self, symbol: str, timeframe: Timeframe, repo) -> TAOutput:
        bars = await self._bar_cache.get_bars(repo, symbol, timeframe.value, count=100)
        highs, lows, closes, volumes = bars.highs, bars.lows, bars.closes, bars.volumes

        if not closes:
            return TAOutput(
                agent=self.name, symbol=symbol, timeframe=timeframe.value,
                indicator="VWAP", value=None,
                confidence=TAConfidence.from_score(0.3),
                metadata={"error": "no_data"},
            )

        # VWAP = sum(typical_price * volume) / sum(volume)
        typical_prices = [(h + l + c) / 3 for h, l, c in zip(highs, lows, closes)]
        total_pv = sum(tp * v for tp, v in zip(typical_prices, volumes))
        total_v = sum(volumes)

        if total_v == 0:
            return TAOutput(
                agent=self.name, symbol=symbol, timeframe=timeframe.value,
                indicator="VWAP", value=None,
                confidence=TAConfidence.from_score(0.5),
                metadata={"error": "zero_volume"},
            )

        vwap = total_pv / total_v
        return TAOutput(
            agent=self.name, symbol=symbol, timeframe=timeframe.value,
            indicator="VWAP",
            value=round(vwap, 4),
            confidence=TAConfidence.from_score(0.98),
        )
