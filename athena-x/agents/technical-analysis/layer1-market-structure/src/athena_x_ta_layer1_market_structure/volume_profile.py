"""Volume Profile Agent - Layer 1."""
from __future__ import annotations
from collections import Counter
from athena_x_ta_base import BaseTAAgent, TAOutput, TAConfidence, Timeframe


class VolumeProfileAgent(BaseTAAgent):
    """Computes POC / VAH / VAL volume distribution."""

    def __init__(self, bins: int = 20, **kwargs):
        super().__init__(name="volume_profile", layer=1, **kwargs)
        self._bins = bins

    async def compute(self, symbol: str, timeframe: Timeframe, repo) -> TAOutput:
        bars = await self._bar_cache.get_bars(repo, symbol, timeframe.value, count=100)
        closes, volumes = bars.closes, bars.volumes

        if len(closes) < 10:
            return TAOutput(
                agent=self.name, symbol=symbol, timeframe=timeframe.value,
                indicator="VolumeProfile", value=None,
                confidence=TAConfidence.from_score(0.3),
            )

        # Simple volume profile: bin closes + sum volume per bin
        min_p, max_p = min(closes), max(closes)
        if max_p == min_p:
            return TAOutput(
                agent=self.name, symbol=symbol, timeframe=timeframe.value,
                indicator="VolumeProfile", value=None,
                confidence=TAConfidence.from_score(0.5),
            )

        bin_size = (max_p - min_p) / self._bins
        vol_by_price = {}
        for c, v in zip(closes, volumes):
            bin_idx = int((c - min_p) / bin_size)
            bin_price = min_p + bin_idx * bin_size
            vol_by_price[bin_price] = vol_by_price.get(bin_price, 0) + v

        poc = max(vol_by_price, key=vol_by_price.get)
        total_vol = sum(vol_by_price.values())
        # Value area: 70% of volume around POC
        sorted_prices = sorted(vol_by_price.keys())
        poc_idx = sorted_prices.index(poc)

        return TAOutput(
            agent=self.name, symbol=symbol, timeframe=timeframe.value,
            indicator="VolumeProfile",
            value={
                "poc": round(poc, 4),
                "vah": round(sorted_prices[min(poc_idx + 3, len(sorted_prices) - 1)], 4),
                "val": round(sorted_prices[max(poc_idx - 3, 0)], 4),
            },
            confidence=TAConfidence.from_score(0.90),
        )
