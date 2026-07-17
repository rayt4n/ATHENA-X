"""Audit trail — logs every validation decision (Stage 3 req 7).

Nothing is silently fixed. Every correction, rejection, warning, and
quarantine is recorded with:
  - provider, validator, rule_triggered
  - original_value, corrected_value
  - timestamp, version, decision

Supports deterministic replay: given a record_id + validator_version,
the audit trail can reproduce the exact decision.
"""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any
from uuid import UUID

from athena_x_runtime_validation_types import AuditEntry, ValidationStatus
from athena_x_runtime_logger import get_logger

log = get_logger("runtime.audit-trail")


class AuditQuery:
    """Query parameters for searching the audit trail."""
    def __init__(
        self,
        provider: str | None = None,
        validator: str | None = None,
        symbol: str | None = None,
        decision: ValidationStatus | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ):
        self.provider = provider
        self.validator = validator
        self.symbol = symbol
        self.decision = decision
        self.start_time = start_time
        self.end_time = end_time

    def matches(self, entry: AuditEntry) -> bool:
        if self.provider and entry.provider != self.provider:
            return False
        if self.validator and entry.validator != self.validator:
            return False
        if self.symbol and entry.symbol != self.symbol:
            return False
        if self.decision and entry.decision != self.decision:
            return False
        if self.start_time and entry.timestamp < self.start_time:
            return False
        if self.end_time and entry.timestamp > self.end_time:
            return False
        return True


class AuditTrail:
    """In-memory + filesystem audit trail.

    In production, this would be backed by a dedicated audit database
    (append-only, tamper-evident). For Stage 3, we use in-memory + optional
    filesystem persistence.
    """

    def __init__(self, persist_path: str | Path | None = None):
        self._entries: list[AuditEntry] = []
        self._lock = RLock()  # reentrant — count_by_* methods called from get_stats
        self._persist_path = Path(persist_path) if persist_path else None
        if self._persist_path:
            self._persist_path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, entry: AuditEntry) -> None:
        """Append an entry to the audit trail."""
        with self._lock:
            self._entries.append(entry)
        log.debug("audit_logged",
                  audit_id=str(entry.audit_id),
                  provider=entry.provider,
                  validator=entry.validator,
                  decision=entry.decision.value)

        if self._persist_path:
            self._persist_entry(entry)

    def _persist_entry(self, entry: AuditEntry) -> None:
        """Append entry to filesystem log (JSONL format)."""
        try:
            with open(self._persist_path, "a", encoding="utf-8") as f:
                f.write(entry.model_dump_json(by_alias=True) + "\n")
        except Exception as e:
            log.error("audit_persist_failed", error=str(e))

    def query(self, q: AuditQuery) -> list[AuditEntry]:
        """Query the audit trail."""
        with self._lock:
            return [e for e in self._entries if q.matches(e)]

    def get_by_record(self, record_id: str) -> list[AuditEntry]:
        """Get all audit entries for a specific record."""
        with self._lock:
            return [e for e in self._entries if e.record_id == record_id]

    def get_by_id(self, audit_id: UUID) -> AuditEntry | None:
        with self._lock:
            for e in self._entries:
                if e.audit_id == audit_id:
                    return e
        return None

    def count(self) -> int:
        with self._lock:
            return len(self._entries)

    def count_by_decision(self) -> dict[str, int]:
        with self._lock:
            counts: dict[str, int] = {}
            for e in self._entries:
                counts[e.decision.value] = counts.get(e.decision.value, 0) + 1
            return counts

    def count_by_provider(self) -> dict[str, int]:
        with self._lock:
            counts: dict[str, int] = {}
            for e in self._entries:
                counts[e.provider] = counts.get(e.provider, 0) + 1
            return counts

    def count_by_validator(self) -> dict[str, int]:
        with self._lock:
            counts: dict[str, int] = {}
            for e in self._entries:
                counts[e.validator] = counts.get(e.validator, 0) + 1
            return counts

    def replay(self, record_id: str, validator_version: str) -> list[AuditEntry]:
        """Deterministic replay — return all decisions for a record at a version."""
        with self._lock:
            return [
                e for e in self._entries
                if e.record_id == record_id
                and e.validator_version == validator_version
            ]

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()
