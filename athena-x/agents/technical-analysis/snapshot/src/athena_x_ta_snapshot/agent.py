"""Technical Snapshot Agent.

Stage 7 additional req: Publishes a single synchronized technical snapshot
after all required analyses complete.

This becomes the standard technical input for:
  - Options Intelligence (Stage 8)
  - Market Intelligence (Stage 10)
  - Forecast Engine (Stage 11)
  - Report Engine (Stage 15)

Downstream modules query ONE snapshot instead of 23 different TA agents.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from athena_x_ta_base import BaseTAAgent, TAOutput, TAConfidence, Timeframe


@dataclass
class TechnicalSnapshot:
    """Synchronized technical snapshot for downstream consumption."""
    symbol: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    # Layer 1: Market Structure
    trend: str = "unknown"
    support: float | None = None
    resistance: float | None = None
    poc: float | None = None  # Volume Profile Point of Control
    # Layer 2: Indicators (latest values for the primary timeframe)
    ema: float | None = None
    rsi: float | None = None
    macd: dict | None = None
    atr: float | None = None
    bollinger: dict | None = None
    adx: float | None = None
    vwap: float | None = None
    # Layer 3: Institutional Analysis
    wyckoff_phase: str | None = None
    smart_money_signal: str | None = None
    entry_signal: str | None = None
    # Layer 4: Consensus
    timeframe_consensus: dict | None = None
    alignment_score: float = 0.0
    # Overall confidence
    overall_confidence: float = 0.0


class TechnicalSnapshotAgent(BaseTAAgent):
    """Publishes a single synchronized technical snapshot.

    Stage 7 rule: Downstream components work from the same consistent view.
    """

    def __init__(self, **kwargs):
        super().__init__(name="technical_snapshot", layer=5, **kwargs)

    async def compute(self, symbol: str, timeframe: Timeframe, repo) -> TAOutput:
        """Compute the full technical snapshot by running all layers."""
        from athena_x_ta_layer1_market_structure import (
            TrendDetectionAgent, SupportResistanceAgent, VolumeProfileAgent,
        )
        from athena_x_ta_layer2_indicators import (
            EMAAgent, RSIAgent, MACDAgent, ATRAgent,
            BollingerAgent, ADXAgent, VWAPAgent,
        )
        from athena_x_ta_layer3_institutional import (
            WyckoffAgent, SmartMoneyAgent, EntryAgent,
        )
        from athena_x_ta_layer4_consensus import TimeframeConsensusAgent

        snapshot = TechnicalSnapshot(symbol=symbol)

        # Layer 1
        trend_result = await TrendDetectionAgent(bar_cache=self._bar_cache).compute(symbol, timeframe, repo)
        snapshot.trend = trend_result.value if isinstance(trend_result.value, str) else "unknown"

        sr_result = await SupportResistanceAgent(bar_cache=self._bar_cache).compute(symbol, timeframe, repo)
        if sr_result.value:
            snapshot.support = sr_result.value.get("support")
            snapshot.resistance = sr_result.value.get("resistance")

        vp_result = await VolumeProfileAgent(bar_cache=self._bar_cache).compute(symbol, timeframe, repo)
        if vp_result.value:
            snapshot.poc = vp_result.value.get("poc")

        # Layer 2
        ema_result = await EMAAgent(bar_cache=self._bar_cache).compute(symbol, timeframe, repo)
        snapshot.ema = ema_result.value if isinstance(ema_result.value, (int, float)) else None

        rsi_result = await RSIAgent(bar_cache=self._bar_cache).compute(symbol, timeframe, repo)
        snapshot.rsi = rsi_result.value if isinstance(rsi_result.value, (int, float)) else None

        macd_result = await MACDAgent(bar_cache=self._bar_cache).compute(symbol, timeframe, repo)
        snapshot.macd = macd_result.value if isinstance(macd_result.value, dict) else None

        atr_result = await ATRAgent(bar_cache=self._bar_cache).compute(symbol, timeframe, repo)
        snapshot.atr = atr_result.value if isinstance(atr_result.value, (int, float)) else None

        bollinger_result = await BollingerAgent(bar_cache=self._bar_cache).compute(symbol, timeframe, repo)
        snapshot.bollinger = bollinger_result.value if isinstance(bollinger_result.value, dict) else None

        adx_result = await ADXAgent(bar_cache=self._bar_cache).compute(symbol, timeframe, repo)
        snapshot.adx = adx_result.value if isinstance(adx_result.value, (int, float)) else None

        vwap_result = await VWAPAgent(bar_cache=self._bar_cache).compute(symbol, timeframe, repo)
        snapshot.vwap = vwap_result.value if isinstance(vwap_result.value, (int, float)) else None

        # Layer 3
        wyckoff_result = await WyckoffAgent(bar_cache=self._bar_cache).compute(symbol, timeframe, repo)
        if wyckoff_result.value and isinstance(wyckoff_result.value, dict):
            snapshot.wyckoff_phase = wyckoff_result.value.get("phase")

        sm_result = await SmartMoneyAgent(bar_cache=self._bar_cache).compute(symbol, timeframe, repo)
        if sm_result.value and isinstance(sm_result.value, dict):
            snapshot.smart_money_signal = "detected" if sm_result.value.get("fvg_detected") else "none"

        entry_result = await EntryAgent(bar_cache=self._bar_cache).compute(symbol, timeframe, repo)
        if entry_result.value and isinstance(entry_result.value, dict):
            snapshot.entry_signal = entry_result.value.get("entry_signal")

        # Layer 4
        consensus_result = await TimeframeConsensusAgent(bar_cache=self._bar_cache).compute(symbol, timeframe, repo)
        if consensus_result.value:
            snapshot.timeframe_consensus = consensus_result.value
            snapshot.alignment_score = consensus_result.value.get("alignment", 0.0)

        # Overall confidence
        snapshot.overall_confidence = 0.85 + snapshot.alignment_score / 100 * 0.1

        return TAOutput(
            agent=self.name, symbol=symbol, timeframe=timeframe.value,
            indicator="TechnicalSnapshot",
            value={
                "symbol": snapshot.symbol,
                "timestamp": snapshot.timestamp.isoformat(),
                "trend": snapshot.trend,
                "support": snapshot.support,
                "resistance": snapshot.resistance,
                "poc": snapshot.poc,
                "ema": snapshot.ema,
                "rsi": snapshot.rsi,
                "macd": snapshot.macd,
                "atr": snapshot.atr,
                "bollinger": snapshot.bollinger,
                "adx": snapshot.adx,
                "vwap": snapshot.vwap,
                "wyckoff_phase": snapshot.wyckoff_phase,
                "smart_money_signal": snapshot.smart_money_signal,
                "entry_signal": snapshot.entry_signal,
                "timeframe_consensus": snapshot.timeframe_consensus,
                "alignment_score": snapshot.alignment_score,
                "overall_confidence": round(snapshot.overall_confidence, 4),
            },
            confidence=TAConfidence.from_score(snapshot.overall_confidence),
            metadata={"layers_consumed": [1, 2, 3, 4]},
        )
