"""Opportunity Ranking Engine - ranks all trade opportunities."""
from __future__ import annotations
from typing import Any
from athena_x_engine_trade_engine.types import TradeRanking


class OpportunityRankingEngine:
    """Ranks trade opportunities by score.

    Stage 12 req: Instead of one trade, rank all opportunities.

    Usage:
        engine = OpportunityRankingEngine()
        rankings = engine.rank([
            TradeRanking(symbol="SPY", trade_type="Calls", score=94),
            TradeRanking(symbol="ES", trade_type="Long", score=90),
            TradeRanking(symbol="QQQ", trade_type="Calls", score=84),
            TradeRanking(symbol="NONE", trade_type="No Trade", score=80),
        ])
        # rankings[0] is the best opportunity
    """
    def rank(self, opportunities: list[TradeRanking]) -> list[TradeRanking]:
        """Rank opportunities by score (highest first)."""
        sorted_ops = sorted(opportunities, key=lambda x: x.score, reverse=True)
        for i, opp in enumerate(sorted_ops):
            opp.rank = i + 1
        return sorted_ops
