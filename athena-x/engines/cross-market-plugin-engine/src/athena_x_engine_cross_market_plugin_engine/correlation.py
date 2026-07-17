"""Correlation Engine - calculates real-time correlation matrix.

Stage 9 req: Every minute calculate ES<->SPY, SPY<->VIX, SPY<->DXY, etc.
Publish only when changes exceed meaningful thresholds.
"""
from __future__ import annotations
import math
from dataclasses import dataclass, field
from threading import RLock
from typing import Any
from athena_x_runtime_logger import get_logger

log = get_logger("correlation-engine")


@dataclass
class CorrelationMatrix:
    """Real-time correlation matrix."""
    pairs: dict[str, float] = field(default_factory=dict)  # "SPY:ES" -> 0.98
    timestamp: str = ""
    changes: list[str] = field(default_factory=list)  # pairs that changed beyond threshold


class CorrelationEngine:
    """Calculates and monitors cross-asset correlations.

    Usage:
        engine = CorrelationEngine()
        engine.update_returns("SPY", [0.01, -0.02, 0.03, ...])
        engine.update_returns("ES", [0.01, -0.02, 0.03, ...])
        matrix = engine.compute_matrix(pairs=[("SPY", "ES"), ("SPY", "VIX")])
    """

    def __init__(self, change_threshold: float = 0.05):
        self._returns: dict[str, list[float]] = {}
        self._previous: dict[str, float] = {}  # previous correlations
        self._threshold = change_threshold
        self._lock = RLock()

    def update_returns(self, symbol: str, returns: list[float]) -> None:
        with self._lock:
            self._returns[symbol] = returns

    def compute_correlation(self, sym_a: str, sym_b: str) -> float | None:
        """Compute Pearson correlation between two symbols."""
        with self._lock:
            rets_a = self._returns.get(sym_a, [])
            rets_b = self._returns.get(sym_b, [])

        if len(rets_a) < 2 or len(rets_b) < 2:
            return None

        n = min(len(rets_a), len(rets_b))
        a = rets_a[-n:]
        b = rets_b[-n:]

        mean_a = sum(a) / n
        mean_b = sum(b) / n

        cov = sum((a[i] - mean_a) * (b[i] - mean_b) for i in range(n)) / n
        std_a = math.sqrt(sum((x - mean_a) ** 2 for x in a) / n)
        std_b = math.sqrt(sum((x - mean_b) ** 2 for x in b) / n)

        if std_a == 0 or std_b == 0:
            return 0.0

        return cov / (std_a * std_b)

    def compute_matrix(self, pairs: list[tuple[str, str]]) -> CorrelationMatrix:
        """Compute correlation for multiple pairs."""
        results: dict[str, float] = {}
        changes: list[str] = []

        for sym_a, sym_b in pairs:
            corr = self.compute_correlation(sym_a, sym_b)
            if corr is not None:
                key = f"{sym_a}:{sym_b}"
                results[key] = round(corr, 4)

                # Check for meaningful change
                prev = self._previous.get(key)
                if prev is not None and abs(corr - prev) > self._threshold:
                    changes.append(f"{key} changed from {prev:.4f} to {corr:.4f}")

                with self._lock:
                    self._previous[key] = corr

        return CorrelationMatrix(
            pairs=results,
            changes=changes,
        )

    def get_stats(self) -> dict:
        with self._lock:
            return {
                "symbols_tracked": len(self._returns),
                "correlations_cached": len(self._previous),
            }
