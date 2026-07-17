"""Market Memory Service - records how similar market conditions behaved historically.

Stage 11 additional req: Before models forecast, they can query:
  "Have we seen this combination of Technical DNA + Options DNA + Market DNA + Narrative DNA before?"
  "What happened next in those cases?"

This historical context strengthens forecasts without coupling to any specific model.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import RLock
from typing import Any
from athena_x_runtime_logger import get_logger

log = get_logger("forecast.market_memory")


@dataclass
class MarketMemoryEntry:
    """A historical market memory entry."""
    timestamp: datetime
    dna_fingerprint: dict[str, Any]  # key features from the 4 DNA objects
    actual_outcome: dict[str, Any]   # what actually happened
    # e.g., {"direction": "bullish", "return_15min": 0.002, "return_1hour": 0.005}


class MarketMemoryService:
    """Records and retrieves historical market condition matches.

    Usage:
        memory = MarketMemoryService()
        memory.record(fingerprint={"trend": "bullish", "regime": "Risk-On"}, outcome={"direction": "bullish"})
        matches = memory.find_similar({"trend": "bullish", "regime": "Risk-On"})
        # matches is a list of historical outcomes for similar conditions
    """

    def __init__(self, max_entries: int = 10000):
        self._entries: list[MarketMemoryEntry] = []
        self._lock = RLock()
        self._max = max_entries

    def record(self, fingerprint: dict[str, Any], outcome: dict[str, Any]) -> None:
        """Record a market condition + its outcome."""
        with self._lock:
            self._entries.append(MarketMemoryEntry(
                timestamp=datetime.now(timezone.utc),
                dna_fingerprint=dict(fingerprint),
                actual_outcome=dict(outcome),
            ))
            if len(self._entries) > self._max:
                self._entries = self._entries[-self._max:]

    def find_similar(self, fingerprint: dict[str, Any], limit: int = 10) -> list[MarketMemoryEntry]:
        """Find historical entries with similar fingerprints."""
        with self._lock:
            scored = []
            for entry in self._entries:
                score = self._similarity_score(fingerprint, entry.dna_fingerprint)
                scored.append((score, entry))
            scored.sort(key=lambda x: x[0], reverse=True)
            return [entry for _, entry in scored[:limit]]

    def _similarity_score(self, a: dict, b: dict) -> float:
        """Compute similarity score between two fingerprints (0..1)."""
        if not a or not b:
            return 0.0
        matches = 0
        total = 0
        for key in a:
            if key in b:
                total += 1
                if a[key] == b[key]:
                    matches += 1
                elif isinstance(a[key], (int, float)) and isinstance(b[key], (int, float)):
                    # Numeric similarity
                    diff = abs(a[key] - b[key])
                    matches += max(0, 1 - diff)
        return matches / total if total > 0 else 0.0

    def get_stats(self) -> dict:
        with self._lock:
            return {"total_entries": len(self._entries)}
