"""Market DNA - single summary object consumed by all downstream AI.

Stage 9 additional req: Continuously summarizes the entire market into one object.

Market DNA
├── Market Regime:    Risk-On
├── Trend:            Bullish
├── Volatility:       Expanding
├── Liquidity:        Neutral
├── Breadth:          Strong
├── Leadership:       Semiconductors
├── Weakest Sector:   Utilities
├── Strongest Asset:  ES
├── Weakest Asset:    VIX
├── Risk Score:       27/100
└── Confidence:       94%

Stage 10 (Forecast), Stage 11 (Probability), Stage 12 (Supervisor) consume this
single object instead of querying dozens of individual plugins.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4
from athena_x_runtime_logger import get_logger
from athena_x_runtime_event_envelope import create_event, EventPriority

log = get_logger("market-intelligence.dna")


@dataclass
class MarketDNA:
    """Single synchronized market summary for downstream AI consumption."""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Regime
    market_regime: str = "unknown"       # Risk-On, Risk-Off, Inflation, Deflation, Liquidity Exp/Contract
    trend: str = "unknown"               # Bullish, Bearish, Ranging
    volatility: str = "unknown"          # Expanding, Contracting, Normal
    liquidity: str = "unknown"           # Neutral, Expanding, Contracting

    # Breadth
    breadth: str = "unknown"             # Strong, Weak, Neutral

    # Leadership
    leadership: str = "unknown"          # Semiconductors, Tech, Financials, ...
    weakest_sector: str | None = None
    strongest_asset: str | None = None
    weakest_asset: str | None = None

    # Risk
    risk_score: int = 50                 # 0 (no risk) to 100 (extreme risk)
    confidence: float = 0.0              # 0..1

    # Correlations
    spy_es_correlation: float | None = None
    spy_vix_correlation: float | None = None
    spy_dxy_correlation: float | None = None

    # Divergences
    divergences: list[str] = field(default_factory=list)

    # Rotation
    rotation_signal: str | None = None   # tech_to_defensive, growth_to_value, ...

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "market_regime": self.market_regime,
            "trend": self.trend,
            "volatility": self.volatility,
            "liquidity": self.liquidity,
            "breadth": self.breadth,
            "leadership": self.leadership,
            "weakest_sector": self.weakest_sector,
            "strongest_asset": self.strongest_asset,
            "weakest_asset": self.weakest_asset,
            "risk_score": self.risk_score,
            "confidence": round(self.confidence, 4),
            "spy_es_correlation": self.spy_es_correlation,
            "spy_vix_correlation": self.spy_vix_correlation,
            "spy_dxy_correlation": self.spy_dxy_correlation,
            "divergences": self.divergences,
            "rotation_signal": self.rotation_signal,
        }


class MarketDNAAgent:
    """Computes the Market DNA from all available market data.

    Stage 9 rule: Downstream AI (Forecast, Probability, Supervisor) consumes
    this single object instead of querying dozens of individual plugins.

    Usage:
        agent = MarketDNAAgent()
        dna = await agent.compute_dna(
            quotes={"SPY": {...}, "ES": {...}, "VIX": {...}, ...},
            returns={"SPY": [...], "ES": [...], ...},
        )
    """

    def __init__(self, event_bus: Any = None):
        self._bus = event_bus
        self._dna_count = 0

    async def compute_dna(
        self,
        quotes: dict[str, dict] | None = None,
        returns: dict[str, list[float]] | None = None,
    ) -> MarketDNA:
        """Compute the Market DNA from current market data."""
        quotes = quotes or {}
        returns = returns or {}
        dna = MarketDNA()

        # Determine trend from SPY/ES
        spy_rets = returns.get("SPY", [])
        if len(spy_rets) >= 10:
            recent = sum(spy_rets[-10:]) / 10
            if recent > 0.001:
                dna.trend = "Bullish"
            elif recent < -0.001:
                dna.trend = "Bearish"
            else:
                dna.trend = "Ranging"

        # Determine volatility from VIX
        vix_quote = quotes.get("VIX", {})
        vix_level = vix_quote.get("last", 15)
        if vix_level > 25:
            dna.volatility = "Expanding"
        elif vix_level < 12:
            dna.volatility = "Contracting"
        else:
            dna.volatility = "Normal"

        # Determine regime
        if dna.trend == "Bullish" and dna.volatility in ("Normal", "Contracting"):
            dna.market_regime = "Risk-On"
        elif dna.trend == "Bearish" or dna.volatility == "Expanding":
            dna.market_regime = "Risk-Off"
        else:
            dna.market_regime = "Neutral"

        # Determine liquidity from rates
        tnx_quote = quotes.get("TNX", {})
        tnx_level = tnx_quote.get("last", 4.5)
        if tnx_level > 4.5:
            dna.liquidity = "Contracting"
        elif tnx_level < 4.0:
            dna.liquidity = "Expanding"
        else:
            dna.liquidity = "Neutral"

        # Determine breadth (simplified — would use A/D ratio in production)
        dna.breadth = "Strong" if dna.trend == "Bullish" else ("Weak" if dna.trend == "Bearish" else "Neutral")

        # Determine leadership
        from athena_x_engine_cross_market_plugin_engine import LeadershipEngine
        leadership_engine = LeadershipEngine()
        for sym, rets in returns.items():
            leadership_engine.update_returns(sym, rets)

        all_symbols = list(returns.keys())
        if all_symbols:
            dna.strongest_asset = leadership_engine.find_strongest(all_symbols)
            dna.weakest_asset = leadership_engine.find_weakest(all_symbols)

        # Determine sector leadership
        sector_symbols = ["XLK", "XLF", "XLV", "XLY", "XLI", "XLE", "XLP", "XLB", "XLU", "XLRE", "XLC"]
        available_sectors = [s for s in sector_symbols if s in returns]
        if available_sectors:
            strongest_sector = leadership_engine.find_strongest(available_sectors)
            weakest_sector = leadership_engine.find_weakest(available_sectors)
            if strongest_sector:
                dna.leadership = strongest_sector
            if weakest_sector:
                dna.weakest_sector = weakest_sector

        # Compute correlations
        from athena_x_engine_cross_market_plugin_engine import CorrelationEngine
        corr_engine = CorrelationEngine()
        for sym, rets in returns.items():
            corr_engine.update_returns(sym, rets)

        dna.spy_es_correlation = corr_engine.compute_correlation("SPY", "ES")
        dna.spy_vix_correlation = corr_engine.compute_correlation("SPY", "VIX")
        dna.spy_dxy_correlation = corr_engine.compute_correlation("SPY", "DXY")

        # Detect divergences
        if dna.spy_vix_correlation is not None and dna.spy_vix_correlation > 0:
            dna.divergences.append("vix_not_confirming")

        # Compute risk score (0 = no risk, 100 = extreme risk)
        risk = 50  # baseline
        if dna.volatility == "Expanding":
            risk += 15
        if dna.trend == "Bearish":
            risk += 15
        if dna.liquidity == "Contracting":
            risk += 10
        if dna.breadth == "Weak":
            risk += 10
        dna.risk_score = min(100, max(0, risk))

        # Compute confidence
        dna.confidence = 0.85
        if len(returns) >= 10:
            dna.confidence += 0.05
        if dna.spy_es_correlation is not None:
            dna.confidence += 0.05
        dna.confidence = min(1.0, dna.confidence)

        self._dna_count += 1

        # Publish event
        if self._bus is not None:
            event = create_event(
                event_type="market:dna_updated",
                source_agent="market-intelligence.dna",
                symbol="*",
                priority=EventPriority.HIGH,
                payload=dna.to_dict(),
            )
            await self._bus.publish(event)

        return dna

    def get_stats(self) -> dict:
        return {"dna_computed": self._dna_count}
