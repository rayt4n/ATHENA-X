"""Quarantine manager — Stage 3 req 10.

Never deletes rejected data. Stores:
  - Reason
  - Provider
  - Raw payload
  - Timestamp
  - Validator
  - Error code

Supports debugging and auditing.
"""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any
from uuid import UUID

from athena_x_runtime_validation_types import (
    QuarantineRecord, ValidationReason, QualityGrade,
)
from athena_x_runtime_logger import get_logger

log = get_logger("validation.quarantine")


class QuarantineManager:
    """Manages quarantined records.

    Records are stored in-memory + optionally persisted to filesystem
    (JSONL format). In production, this would be a dedicated quarantine
    database (append-only).
    """

    def __init__(self, persist_path: str | Path | None = None):
        self._records: list[QuarantineRecord] = []
        self._lock = RLock()  # reentrant — get_stats calls count_by_* internally
        self._persist_path = Path(persist_path) if persist_path else None
        if self._persist_path:
            self._persist_path.parent.mkdir(parents=True, exist_ok=True)

    def quarantine(self, record: QuarantineRecord) -> None:
        """Add a record to quarantine."""
        with self._lock:
            self._records.append(record)
        log.info("record_quarantined",
                 quarantine_id=str(record.quarantine_id),
                 provider=record.provider,
                 symbol=record.symbol,
                 reason=record.reason.value,
                 validator=record.validator)

        if self._persist_path:
            self._persist(record)

    def _persist(self, record: QuarantineRecord) -> None:
        try:
            with open(self._persist_path, "a", encoding="utf-8") as f:
                f.write(record.model_dump_json(by_alias=True) + "\n")
        except Exception as e:
            log.error("quarantine_persist_failed", error=str(e))

    def list_all(self) -> list[QuarantineRecord]:
        with self._lock:
            return list(self._records)

    def list_by_provider(self, provider: str) -> list[QuarantineRecord]:
        with self._lock:
            return [r for r in self._records if r.provider == provider]

    def list_by_reason(self, reason: ValidationReason) -> list[QuarantineRecord]:
        with self._lock:
            return [r for r in self._records if r.reason == reason]

    def list_by_symbol(self, symbol: str) -> list[QuarantineRecord]:
        with self._lock:
            return [r for r in self._records if r.symbol == symbol]

    def count(self) -> int:
        with self._lock:
            return len(self._records)

    def count_by_provider(self) -> dict[str, int]:
        with self._lock:
            counts: dict[str, int] = {}
            for r in self._records:
                counts[r.provider] = counts.get(r.provider, 0) + 1
            return counts

    def count_by_reason(self) -> dict[str, int]:
        with self._lock:
            counts: dict[str, int] = {}
            for r in self._records:
                key = r.reason.value
                counts[key] = counts.get(key, 0) + 1
            return counts

    def get_stats(self) -> dict:
        """Self-monitoring metrics (Stage 3 req 8)."""
        with self._lock:
            total = len(self._records)
            avg_confidence = (
                sum(r.confidence_score for r in self._records) / total
                if total > 0 else 0.0
            )
            return {
                "quarantine_size": total,
                "average_confidence": avg_confidence,
                "by_provider": self.count_by_provider(),
                "by_reason": self.count_by_reason(),
            }

    def clear(self) -> None:
        with self._lock:
            self._records.clear()
