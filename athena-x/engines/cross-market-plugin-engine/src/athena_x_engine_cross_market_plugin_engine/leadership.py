"""Leadership Engine - determines who is leading, lagging, or diverging.

Stage 9 req: Continuously answer:
  - Is NVDA leading QQQ?
  - Is QQQ leading SPY?
  - Is SOXX stronger than XLK?
  - Is VIX confirming?
"""
from __future__ import annotations
from dataclasses import dataclass, field
from threading import RLock
from typing import Any
from athena_x_runtime_logger import get_logger

log = get_logger("leadership-engine")


@dataclass
class LeadershipResult:
    """Result of a leadership analysis."""
    leader: str | None = None
    lagger: str | None = None
    signal: str = "neutral"  # "leading", "lagging", "diverging", "neutral"
    strength: float = 0.0  # 0..1
    description: str = ""


class LeadershipEngine:
    """Determines market leadership between instruments.

    Usage:
        engine = LeadershipEngine()
        engine.update_returns("NVDA", [0.02, 0.03, ...])
        engine.update_returns("QQQ", [0.01, 0.02, ...])
        result = engine.analyze_leadership("NVDA", "QQQ")
        # result.leader == "NVDA"
    """

    def __init__(self, lookback: int = 20):
        self._returns: dict[str, list[float]] = {}
        self._lookback = lookback
        self._lock = RLock()

    def update_returns(self, symbol: str, returns: list[float]) -> None:
        with self._lock:
            self._returns[symbol] = returns[-self._lookback:]

    def analyze_leadership(self, sym_a: str, sym_b: str) -> LeadershipResult:
        """Analyze which symbol is leading."""
        with self._lock:
            rets_a = self._returns.get(sym_a, [])
            rets_b = self._returns.get(sym_b, [])

        if len(rets_a) < 5 or len(rets_b) < 5:
            return LeadershipResult(description="insufficient data")

        # Compare recent performance
        recent_a = sum(rets_a[-5:]) / 5
        recent_b = sum(rets_b[-5:]) / 5

        # Check for lead/lag: does A move before B?
        # Simple approach: if A's return is more extreme, A is leading
        if abs(recent_a) > abs(recent_b) * 1.2:
            leader = sym_a
            lagger = sym_b
            signal = "leading"
            strength = min(1.0, abs(recent_a) / (abs(recent_b) + 0.001))
        elif abs(recent_b) > abs(recent_a) * 1.2:
            leader = sym_b
            lagger = sym_a
            signal = "leading"
            strength = min(1.0, abs(recent_b) / (abs(recent_a) + 0.001))
        elif (recent_a > 0) != (recent_b > 0):
            leader = sym_a if abs(recent_a) > abs(recent_b) else sym_b
            lagger = sym_b if leader == sym_a else sym_a
            signal = "diverging"
            strength = 0.5
        else:
            leader = None
            lagger = None
            signal = "neutral"
            strength = 0.0

        return LeadershipResult(
            leader=leader,
            lagger=lagger,
            signal=signal,
            strength=round(strength, 4),
            description=f"{leader} {'leading' if leader else 'neutral'} {lagger}",
        )

    def find_strongest(self, symbols: list[str]) -> str | None:
        """Find the strongest performing symbol."""
        with self._lock:
            best: tuple[str, float] | None = None
            for sym in symbols:
                rets = self._returns.get(sym, [])
                if len(rets) >= 5:
                    recent = sum(rets[-5:]) / 5
                    if best is None or recent > best[1]:
                        best = (sym, recent)
            return best[0] if best else None

    def find_weakest(self, symbols: list[str]) -> str | None:
        """Find the weakest performing symbol."""
        with self._lock:
            worst: tuple[str, float] | None = None
            for sym in symbols:
                rets = self._returns.get(sym, [])
                if len(rets) >= 5:
                    recent = sum(rets[-5:]) / 5
                    if worst is None or recent < worst[1]:
                        worst = (sym, recent)
            return worst[0] if worst else None
