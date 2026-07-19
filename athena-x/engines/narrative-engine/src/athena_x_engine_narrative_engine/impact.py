"""Market Impact Engine - computes directional relationships.

Stage 10: No forecasts. Only directional relationships.

Example:
  Event: US CPI
  -> Bonds up -> DXY up -> VIX up -> ES down
  Probability: 82%
"""
from __future__ import annotations
from typing import Any
from athena_x_plugin_news_base import NewsEvent, NewsImpact, NewsCategory
from athena_x_runtime_logger import get_logger

log = get_logger("narrative.impact")


# Impact chains by category (directional, not forecasts)
IMPACT_CHAINS = {
    NewsCategory.ECONOMIC: {
        "inflation_high": [
            {"asset": "Bonds", "direction": "down"},   # yields up
            {"asset": "DXY", "direction": "up"},
            {"asset": "VIX", "direction": "up"},
            {"asset": "ES", "direction": "down"},
            {"asset": "Gold", "direction": "up"},
        ],
        "inflation_low": [
            {"asset": "Bonds", "direction": "up"},      # yields down
            {"asset": "DXY", "direction": "down"},
            {"asset": "VIX", "direction": "down"},
            {"asset": "ES", "direction": "up"},
            {"asset": "Gold", "direction": "down"},
        ],
    },
    NewsCategory.FED: {
        "hawkish": [
            {"asset": "Bonds", "direction": "down"},
            {"asset": "DXY", "direction": "up"},
            {"asset": "VIX", "direction": "up"},
            {"asset": "ES", "direction": "down"},
            {"asset": "QQQ", "direction": "down"},
        ],
        "dovish": [
            {"asset": "Bonds", "direction": "up"},
            {"asset": "DXY", "direction": "down"},
            {"asset": "VIX", "direction": "down"},
            {"asset": "ES", "direction": "up"},
            {"asset": "QQQ", "direction": "up"},
        ],
    },
    NewsCategory.GEOPOLITICAL: {
        "default": [
            {"asset": "VIX", "direction": "up"},
            {"asset": "Gold", "direction": "up"},
            {"asset": "Oil", "direction": "up"},
            {"asset": "ES", "direction": "down"},
        ],
    },
    NewsCategory.SEMICONDUCTOR: {
        "positive": [
            {"asset": "SOXX", "direction": "up"},
            {"asset": "QQQ", "direction": "up"},
            {"asset": "NVDA", "direction": "up"},
        ],
        "negative": [
            {"asset": "SOXX", "direction": "down"},
            {"asset": "QQQ", "direction": "down"},
            {"asset": "NVDA", "direction": "down"},
        ],
    },
    NewsCategory.ENERGY: {
        "supply_cut": [
            {"asset": "Oil", "direction": "up"},
            {"asset": "XLE", "direction": "up"},
            {"asset": "ES", "direction": "down"},
        ],
    },
}


class MarketImpactEngine:
    """Computes directional market impact for events.

    Stage 10 rule: No forecasts. Only directional relationships.
    """

    def assess_impact(self, event: NewsEvent) -> NewsImpact:
        """Assess the market impact of an event."""
        chain = self._get_impact_chain(event)
        probability = self._estimate_probability(event, chain)
        confidence = self._estimate_confidence(event)

        return NewsImpact(
            event_id=event.event_id,
            impact_chain=chain,
            probability=probability,
            confidence=confidence,
        )

    def _get_impact_chain(self, event: NewsEvent) -> list[dict]:
        """Get the directional impact chain for an event."""
        category_chains = IMPACT_CHAINS.get(event.category, {})

        # Determine sub-type from headline
        headline_lower = event.headline.lower()
        if event.category == NewsCategory.ECONOMIC:
            if any(w in headline_lower for w in ["higher", "hot", "above", "beat"]):
                return category_chains.get("inflation_high", [])
            elif any(w in headline_lower for w in ["lower", "cool", "below", "miss"]):
                return category_chains.get("inflation_low", [])
        elif event.category == NewsCategory.FED:
            if any(w in headline_lower for w in ["hawkish", "higher", "hike", "hold"]):
                return category_chains.get("hawkish", [])
            elif any(w in headline_lower for w in ["dovish", "cut", "lower", "pause"]):
                return category_chains.get("dovish", [])
        elif event.category == NewsCategory.SEMICONDUCTOR:
            if any(w in headline_lower for w in ["beat", "strong", "upgrade", "surge"]):
                return category_chains.get("positive", [])
            elif any(w in headline_lower for w in ["miss", "weak", "downgrade", "fall"]):
                return category_chains.get("negative", [])

        return category_chains.get("default", [])

    def _estimate_probability(self, event: NewsEvent, chain: list[dict]) -> float:
        """Estimate the probability of the impact chain occurring."""
        if not chain:
            return 0.3
        # Higher importance = higher probability
        prob_map = {"critical": 0.85, "high": 0.75, "medium": 0.60, "low": 0.40}
        return prob_map.get(event.importance.value, 0.50)

    def _estimate_confidence(self, event: NewsEvent) -> float:
        """Estimate confidence in the impact assessment."""
        # More symbols = more context = higher confidence
        base = 0.6
        if len(event.symbols) > 0:
            base += 0.1
        if len(event.related_assets) > 2:
            base += 0.1
        if event.importance.value in ("critical", "high"):
            base += 0.1
        return min(1.0, base)
