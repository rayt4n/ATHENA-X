"""Feature Fusion Layer - converts 4 DNA objects into canonical feature vector.

Stage 11 req: Before any model runs, all four DNA objects are converted
into a single canonical feature vector. This ensures every model receives
identical inputs.
"""
from __future__ import annotations
from typing import Any
from athena_x_plugin_forecast_base import ForecastInput, ForecastHorizon


class FeatureFusion:
    """Fuses Technical DNA, Options DNA, Market DNA, Narrative DNA.

    Usage:
        fusion = FeatureFusion()
        features = fusion.fuse(
            technical_dna={...},
            options_dna={...},
            market_dna={...},
            narrative_dna={...},
            symbol="SPY",
        )
        # features is a flat dict that any model can consume
    """

    def fuse(
        self,
        technical_dna: dict | None = None,
        options_dna: dict | None = None,
        market_dna: dict | None = None,
        narrative_dna: dict | None = None,
        symbol: str = "SPY",
        horizon: ForecastHorizon = ForecastHorizon.NEXT_15MIN,
    ) -> ForecastInput:
        """Fuse the 4 DNA objects into a canonical feature vector."""
        features: dict[str, Any] = {}

        # Technical DNA features
        td = technical_dna or {}
        features["trend"] = td.get("trend", "unknown")
        features["rsi"] = td.get("rsi", 50)
        features["ema"] = td.get("ema", 0)
        features["macd_histogram"] = td.get("macd", {}).get("histogram", 0) if isinstance(td.get("macd"), dict) else 0
        features["atr"] = td.get("atr", 0)
        features["adx"] = td.get("adx", 25)
        features["alignment_score"] = td.get("alignment_score", 50)
        features["bollinger_percent_b"] = td.get("bollinger", {}).get("percent_b", 0.5) if isinstance(td.get("bollinger"), dict) else 0.5

        # Options DNA features
        od = options_dna or {}
        features["dealer_gamma"] = od.get("dealer_gamma", "unknown")
        features["gamma_flip"] = od.get("gamma_flip_level", 0)
        features["iv_regime"] = od.get("iv_regime", "unknown")
        features["iv_crush_risk"] = od.get("iv_crush_risk", 0)
        features["expected_move"] = od.get("expected_move", 0)
        features["positioning"] = od.get("positioning", "unknown")
        features["intraday_risk"] = od.get("intraday_risk", "unknown")

        # Market DNA features
        md = market_dna or {}
        features["market_regime"] = md.get("market_regime", "unknown")
        features["volatility"] = md.get("volatility", "unknown")
        features["liquidity"] = md.get("liquidity", "unknown")
        features["breadth"] = md.get("breadth", "unknown")
        features["leadership"] = md.get("leadership", "unknown")
        features["risk_score"] = md.get("risk_score", 50)
        features["spy_es_correlation"] = md.get("spy_es_correlation", 0.95) or 0.95
        features["spy_vix_correlation"] = md.get("spy_vix_correlation", -0.7) or -0.7

        # Narrative DNA features
        nd = narrative_dna or {}
        features["primary_driver"] = nd.get("primary_driver", "unknown")
        features["current_theme"] = nd.get("current_theme", "unknown")
        features["narrative_confidence"] = nd.get("confidence", 0.5)
        features["active_event_count"] = len(nd.get("active_events", []))
        features["catalyst_count"] = len(nd.get("upcoming_catalysts", []))

        # Session context
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        features["hour"] = now.hour
        features["minute"] = now.minute
        features["day_of_week"] = now.weekday()

        return ForecastInput(
            symbol=symbol,
            timestamp=now,
            features=features,
            horizon=horizon,
        )
