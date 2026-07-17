"""Audit Trail - immutable log of all operational changes.

Stage 13 req: Log everything for full reproducibility.
"""
from __future__ import annotations
from datetime import datetime, timezone
from threading import RLock
from typing import Any
from athena_x_engine_governance_engine.types import AuditEntry
from athena_x_runtime_logger import get_logger

log = get_logger("governance.audit_trail")


class AuditTrail:
    """Immutable audit trail for all operational changes.

    Records:
      - Configuration changes
      - Plugin updates
      - AI model changes
      - Weight adjustments
      - Provider failovers
      - Manual overrides
      - System restarts
    """

    def __init__(self, max_entries: int = 10000):
        self._entries: list[AuditEntry] = []
        self._lock = RLock()
        self._max = max_entries

    def record(self, action: str, actor: str = "system", details: str = "") -> AuditEntry:
        """Record an audit entry."""
        with self._lock:
            entry = AuditEntry(
                timestamp=datetime.now(timezone.utc),
                action=action,
                actor=actor,
                details=details,
            )
            self._entries.append(entry)
            if len(self._entries) > self._max:
                self._entries = self._entries[-self._max:]

            log.info("audit_recorded", action=action, actor=actor)
            return entry

    def get_entries(self, limit: int = 50, action_filter: str | None = None) -> list[AuditEntry]:
        with self._lock:
            entries = list(self._entries)
        if action_filter:
            entries = [e for e in entries if action_filter in e.action]
        return entries[-limit:]

    def count(self) -> int:
        with self._lock:
            return len(self._entries)
