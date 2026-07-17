"""Base repository with common functionality."""
from __future__ import annotations
from abc import ABC
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from .protocols import WriteResult, RepositoryError


class BaseRepository(ABC):
    """Base class for repository implementations.

    Provides:
      - Record ID generation
      - Timestamp helpers
      - Supersession tracking
    """

    schema_name: str = "unknown"

    def _generate_record_id(self) -> str:
        """Generate a unique record ID."""
        return str(uuid4())

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def _make_write_result(
        self, record_id: str, table: str,
        superseded_record_id: str | None = None,
        event_published: bool = False,
    ) -> WriteResult:
        return WriteResult(
            record_id=record_id,
            schema=self.schema_name,
            table=table,
            written_at=self._now(),
            superseded_record_id=superseded_record_id,
            event_published=event_published,
        )
