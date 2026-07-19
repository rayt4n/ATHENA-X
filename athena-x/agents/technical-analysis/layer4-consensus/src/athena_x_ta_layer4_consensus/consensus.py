"""Multi-Timeframe Consensus Agent - Layer 4.

Stage 7 req: One agent produces a synchronized view across 8 timeframes.

Output example:
  Long-term Trend:  Bullish
  Intermediate:     Bullish
  Intraday:          Bearish Pullback
  Alignment:         82%
  Conflict:          15M diverging from 1H

Downstream modules read this single consensus instead of reconciling 8 timeframes.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

from athena_x_ta_base import BaseTAAgent, TAOutput, TAConfidence, Timeframe, STANDARD_TIMEFRAMES


@dataclass
class ConsensusResult:
    """Result of multi-timeframe consensus."""
    long_term_trend: str = "unknown"      # Monthly + Weekly
    intermediate_trend: str = "unknown"   # Daily + 4H
    intraday_trend: str = "unknown"       # 1H + 30M + 15M + 5M + 1M
    alignment_score: float = 0.0          # 0-100
    conflicts: list[str] = field(default_factory=list)
    breakdown: dict[str, str] = field(default_factory=dict)


class TimeframeConsensusAgent(BaseTAAgent):
    """Produces a synchronized multi-timeframe consensus view.

    Instead of every AI looking at every timeframe independently,
    this agent produces a single unified view.

    Stage 7 rule: Downstream modules read this single consensus.
    """

    def __init__(self, **kwargs):
        super().__init__(name="timeframe_consensus", layer=4, **kwargs)

    async def compute(self, symbol: str, timeframe: Timeframe, repo) -> TAOutput:
        # Fetch trend for each timeframe
        from athena_x_ta_layer1_market_structure import TrendDetectionAgent
        trend_agent = TrendDetectionAgent(bar_cache=self._bar_cache)

        trends: dict[str, str] = {}
        for tf in STANDARD_TIMEFRAMES:
            result = await trend_agent.compute(symbol, tf, repo)
            trends[tf.value] = result.value if result.value else "unknown"

        # Classify by horizon
        long_term = self._classify_group(trends, ["1M", "1W"])
        intermediate = self._classify_group(trends, ["1D", "4H"])
        intraday = self._classify_group(trends, ["1H", "30M", "15M", "5M", "1m"])

        # Calculate alignment score
        all_trends = list(trends.values())
        bullish_count = sum(1 for t in all_trends if t == "bullish")
        bearish_count = sum(1 for t in all_trends if t == "bearish")
        total = len(all_trends)
        alignment = max(bullish_count, bearish_count) / total * 100 if total > 0 else 0

        # Detect conflicts
        conflicts = []
        if trends.get("15M") != trends.get("1H"):
            conflicts.append(f"15M diverging from 1H")
        if trends.get("5M") != trends.get("15M"):
            conflicts.append(f"5M diverging from 15M")

        consensus = ConsensusResult(
            long_term_trend=long_term,
            intermediate_trend=intermediate,
            intraday_trend=intraday,
            alignment_score=round(alignment, 1),
            conflicts=conflicts,
            breakdown=trends,
        )

        confidence_score = alignment / 100 * 0.3 + 0.6

        return TAOutput(
            agent=self.name, symbol=symbol, timeframe="ALL",
            indicator="TimeframeConsensus",
            value={
                "long_term": long_term,
                "intermediate": intermediate,
                "intraday": intraday,
                "alignment": round(alignment, 1),
                "conflicts": conflicts,
                "breakdown": trends,
            },
            confidence=TAConfidence.from_score(confidence_score),
            metadata={"timeframes_evaluated": len(trends)},
        )

    def _classify_group(self, trends: dict, tfs: list[str]) -> str:
        """Classify a group of timeframes into a single trend."""
        group_trends = [trends.get(tf, "unknown") for tf in tfs]
        if all(t == "bullish" for t in group_trends):
            return "bullish"
        if all(t == "bearish" for t in group_trends):
            return "bearish"
        if "bullish" in group_trends and "bearish" in group_trends:
            return "mixed"
        return "ranging"
