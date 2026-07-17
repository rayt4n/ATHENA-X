"""Trade Qualification Engine - determines if we should trade at all.

Stage 12 req: Most systems never say 'do nothing.' Yours should.

Outputs: NO_TRADE, WATCH, PREPARE, READY, ACTIVE
"""
from __future__ import annotations
from typing import Any
from athena_x_engine_trade_engine.types import TradeStatus, TradeAlignment


class TradeQualificationEngine:
    """Determines whether to trade, watch, or stand aside.

    Usage:
        engine = TradeQualificationEngine()
        status = engine.qualify(
            alignment=TradeAlignment(technical=True, options=True, market=True, narrative=False, forecast=True),
            risk_score=30,
            timing_score=75,
        )
        # status might be READY
    """

    def qualify(
        self,
        alignment: TradeAlignment,
        risk_score: int,
        timing_score: int,
        entry_quality: int = 50,
    ) -> TradeStatus:
        """Determine the trade status.

        Args:
            alignment: alignment between the 5 DNA objects
            risk_score: 0 (no risk) to 100 (extreme risk)
            timing_score: 0-100 timing quality
            entry_quality: 0-100 entry quality score

        Returns:
            TradeStatus (NO_TRADE, WATCH, PREPARE, READY, ACTIVE)
        """
        align_score = alignment.score

        # Hard rules
        if risk_score > 80:
            return TradeStatus.NO_TRADE  # too risky

        if align_score < 0.4:
            return TradeStatus.NO_TRADE  # not enough alignment

        if align_score < 0.6:
            return TradeStatus.WATCH  # partial alignment

        # Good alignment
        if timing_score >= 75 and entry_quality >= 70 and risk_score <= 50:
            return TradeStatus.ACTIVE

        if timing_score >= 60 and entry_quality >= 60:
            return TradeStatus.READY

        if timing_score >= 40:
            return TradeStatus.PREPARE

        return TradeStatus.WATCH
