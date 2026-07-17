"""Market Intelligence Hub - aggregates all cross-market intelligence.

Stage 9 req: One hub that collects all market monitor, correlation,
leadership, regime, rotation, and divergence signals into a unified view.
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any
from athena_x_runtime_logger import get_logger

log = get_logger("market-intelligence.hub")


class MarketIntelligenceHub:
    """Aggregates all cross-market intelligence into a unified view.

    Usage:
        hub = MarketIntelligenceHub()
        hub.update_quote("SPY", {"last": 450.0, "change_pct": 0.5})
        hub.update_quote("ES", {"last": 4520.0, "change_pct": 0.4})
        snapshot = hub.get_snapshot()
    """

    def __init__(self):
        self._quotes: dict[str, dict] = {}
        self._returns: dict[str, list[float]] = {}
        self._signals: list[dict] = []
        self._last_snapshot: datetime | None = None

    def update_quote(self, symbol: str, quote: dict) -> None:
        """Update the latest quote for a symbol."""
        self._quotes[symbol] = quote
        # Track returns
        change_pct = quote.get("change_pct", 0)
        if symbol not in self._returns:
            self._returns[symbol] = []
        self._returns[symbol].append(change_pct / 100)
        # Keep last 100 returns
        if len(self._returns[symbol]) > 100:
            self._returns[symbol] = self._returns[symbol][-100:]

    def add_signal(self, signal: dict) -> None:
        """Add a cross-market signal (divergence, leadership change, etc.)."""
        self._signals.append(signal)
        if len(self._signals) > 1000:
            self._signals = self._signals[-500:]

    def get_snapshot(self) -> dict:
        """Get a synchronized snapshot of all market data."""
        self._last_snapshot = datetime.now(timezone.utc)
        return {
            "timestamp": self._last_snapshot.isoformat(),
            "quotes": dict(self._quotes),
            "symbols_tracked": len(self._quotes),
            "recent_signals": self._signals[-10:],
        }

    def get_quotes(self) -> dict[str, dict]:
        return dict(self._quotes)

    def get_returns(self) -> dict[str, list[float]]:
        return dict(self._returns)

    def get_stats(self) -> dict:
        return {
            "symbols_tracked": len(self._quotes),
            "signals_collected": len(self._signals),
            "last_snapshot": self._last_snapshot.isoformat() if self._last_snapshot else None,
        }
