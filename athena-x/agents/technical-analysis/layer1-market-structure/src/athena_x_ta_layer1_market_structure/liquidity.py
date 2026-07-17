"""Liquidity Agent - Layer 1."""
from __future__ import annotations
from athena_x_ta_base import BaseTAAgent, TAOutput, TAConfidence, Timeframe


class LiquidityAgent(BaseTAAgent):
    """Detects liquidity pools and voids."""

    def __init__(self, **kwargs):
        super().__init__(name="liquidity", layer=1, **kwargs)

    async def compute(self, symbol: str, timeframe: Timeframe, repo) -> TAOutput:
        bars = await self._bar_cache.get_bars(repo, symbol, timeframe.value, count=50)
        volumes, closes = bars.volumes, bars.closes

        if len(volumes) < 10:
            return TAOutput(
                agent=self.name, symbol=symbol, timeframe=timeframe.value,
                indicator="Liquidity", value=None,
                confidence=TAConfidence.from_score(0.3),
            )

        avg_vol = sum(volumes) / len(volumes)
        high_vol_levels = [
            {"price": closes[i], "volume": volumes[i]}
            for i in range(len(volumes))
            if volumes[i] > avg_vol * 1.5
        ]

        return TAOutput(
            agent=self.name, symbol=symbol, timeframe=timeframe.value,
            indicator="Liquidity",
            value={"liquidity_pools": high_vol_levels[-5:], "avg_volume": avg_vol},
            confidence=TAConfidence.from_score(0.82),
        )
