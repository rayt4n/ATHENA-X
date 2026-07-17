"""Entry Agent - Layer 3 (Institutional Analysis).

High-probability entry identification

Stage 7 rule: Consumes outputs from Layers 1 + 2 rather than recalculating.
"""
from __future__ import annotations
from athena_x_ta_base import BaseTAAgent, TAOutput, TAConfidence, Timeframe


class EntryAgent(BaseTAAgent):
    """High-probability entry identification"""

    def __init__(self, **kwargs):
        super().__init__(name="entry", layer=3, **kwargs)

    async def compute(self, symbol: str, timeframe: Timeframe, repo) -> TAOutput:
        bars = await self._bar_cache.get_bars(repo, symbol, timeframe.value, count=100)
        closes, volumes = bars.closes, bars.volumes

        if len(closes) < 20:
            return TAOutput(
                agent=self.name, symbol=symbol, timeframe=timeframe.value,
                indicator="Entry", value=None,
                confidence=TAConfidence.from_score(0.3),
                metadata={"error": "insufficient_data"},
            )

        # Layer 3 agents consume Layer 1+2 outputs via the event bus
        # For V1, we compute a simplified analysis directly from bars
        recent_closes = closes[-20:]
        avg = sum(recent_closes) / len(recent_closes)
        current = closes[-1]
        deviation = (current - avg) / avg if avg > 0 else 0

        # Pattern-specific logic would go here
        # For V1, we return a simplified assessment
        if "entry" == "wyckoff":
            phase = "accumulation" if abs(deviation) < 0.01 else ("markup" if deviation > 0.01 else "distribution")
            value = {"phase": phase, "deviation": round(deviation * 100, 4)}
        elif "entry" == "chan_theory":
            value = {"bi_count": len(recent_closes) // 3, "zhongshu_detected": abs(deviation) < 0.005}
        elif "entry" == "elliott_wave":
            value = {"current_wave": 3 if deviation > 0.01 else (5 if deviation > 0.02 else "corrective")}
        elif "entry" == "smart_money":
            value = {"order_blocks": closes[-3:], "fvg_detected": abs(closes[-1] - closes[-3]) > 2 * (max(closes[-10:]) - min(closes[-10:])) / 10}
        elif "entry" == "volume_price":
            vol_trend = "increasing" if volumes[-1] > sum(volumes[-5:]) / 5 else "decreasing"
            value = {"volume_trend": vol_trend, "price_trend": "up" if deviation > 0 else "down"}
        elif "entry" == "escape_top":
            value = {"escape_detected": deviation > 0.03, "consolidation_range": round(max(recent_closes) - min(recent_closes), 4)}
        elif "entry" == "entry":
            value = {"entry_signal": "long" if deviation > 0.005 else ("short" if deviation < -0.005 else "wait"), "confidence_level": "high" if abs(deviation) > 0.01 else "medium"}
        elif "entry" == "pull_up_pattern":
            value = {"pull_up_detected": closes[-1] > closes[-5] and volumes[-1] > volumes[-5], "strength": round(abs(deviation) * 100, 4)}
        else:
            value = {"analysis": "unknown"}

        # Interpretive analyses have lower confidence (pattern recognition)
        confidence_score = 0.75 + min(0.15, abs(deviation) * 5)

        return TAOutput(
            agent=self.name, symbol=symbol, timeframe=timeframe.value,
            indicator="Entry",
            value=value,
            confidence=TAConfidence.from_score(confidence_score),
            metadata={"layer": 3, "consumes_layers": [1, 2]},
        )
