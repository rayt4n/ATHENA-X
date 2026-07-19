"""Duplicate detector — Stage 3 req 2.7.

Rejects:
  - Same provider
  - Same timestamp
  - Same symbol
  - Same payload

Avoids duplicated events.

Implementation: hash(provider + symbol + timestamp + canonical payload).
Maintains an LRU cache of recent hashes.
"""
from __future__ import annotations
import hashlib
import json
from collections import OrderedDict
from threading import Lock
from typing import Any

from athena_x_validator_base import BaseValidator, ValidatorConfig
from athena_x_runtime_validation_types import (
    ValidationResult, ValidationContext, ValidationStatus, ValidationReason,
)


class DuplicateDetector(BaseValidator):
    """Detects duplicate records (same provider + ts + symbol + payload)."""

    def __init__(self, cache_size: int = 10000):
        super().__init__(ValidatorConfig(
            name="duplicate-detector",
            blocking=True,
        ))
        self._cache_size = cache_size
        self._seen: OrderedDict[str, None] = OrderedDict()
        self._lock = Lock()

    async def validate(self, record: Any, context: ValidationContext) -> ValidationResult:
        """Check if the record is a duplicate."""
        if not isinstance(record, dict):
            return self._passed("non-dict, skipping")

        # Build a canonical hash
        record_hash = self._hash(record, context)

        with self._lock:
            if record_hash in self._seen:
                return self._reject(
                    ValidationReason.DUPLICATE_PAYLOAD,
                    f"Duplicate record (provider={context.provider}, symbol={context.symbol})",
                )

            # Add to cache
            self._seen[record_hash] = None
            # Evict oldest if over capacity
            while len(self._seen) > self._cache_size:
                self._seen.popitem(last=False)

        return self._passed("unique record")

    def _hash(self, record: dict, context: ValidationContext) -> str:
        """Build a canonical hash of provider + symbol + timestamp + payload."""
        ts = record.get("timestamp", "")
        # Canonicalize payload (sorted keys, stable JSON)
        payload_str = json.dumps(record, sort_keys=True, default=str)
        key = f"{context.provider}|{context.symbol}|{ts}|{payload_str}"
        return hashlib.sha256(key.encode()).hexdigest()

    def get_stats(self) -> dict:
        with self._lock:
            return {
                "cache_size": len(self._seen),
                "max_cache_size": self._cache_size,
            }
