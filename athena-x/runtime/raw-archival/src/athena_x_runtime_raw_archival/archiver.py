"""Raw payload archival — Stage 2 req 1.6.

Every raw payload is archived before parsing. Directory structure:
    raw_landing/
    └── <provider>/
        └── <yyyy>/
            └── <mm>/
                └── <dd>/
                    └── <hh>/
                        └── <uuid>.json

Never discards original data. If parsing fails later, the source is still
available for replay/audit.
"""
from __future__ import annotations
import json
import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from athena_x_runtime_logger import get_logger

log = get_logger("runtime.raw-archival")


@dataclass(frozen=True)
class ArchivedFile:
    """Metadata about an archived raw payload."""
    path: str
    provider: str
    size_bytes: int
    archived_at: datetime


class RawArchiver:
    """Archives raw payloads to the filesystem.

    Usage:
        archiver = RawArchiver(base_path="/var/lib/athena-x/raw_landing")
        archived = archiver.archive(
            provider="yahoo",
            payload={"symbol": "NVDA", "last": 128.45, ...},
            timestamp=datetime.now(timezone.utc),
        )
        # archived.path = "/var/lib/athena-x/raw_landing/yahoo/2026/07/17/13/<uuid>.json"
    """

    def __init__(self, base_path: str | Path = "raw_landing"):
        self._base_path = Path(base_path)
        self._base_path.mkdir(parents=True, exist_ok=True)

    def archive(
        self,
        *,
        provider: str,
        payload: Any,
        timestamp: datetime | None = None,
    ) -> ArchivedFile:
        """Archive a raw payload.

        Args:
            provider: provider slug (e.g., "yahoo", "finnhub")
            payload: any JSON-serializable payload
            timestamp: optional — defaults to now (UTC)

        Returns:
            ArchivedFile with the path where the payload was written.
        """
        ts = timestamp or datetime.now(timezone.utc)
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)

        # Build directory: base/provider/yyyy/mm/dd/hh/
        dir_path = self._base_path / provider / ts.strftime("%Y/%m/%d/%H")
        dir_path.mkdir(parents=True, exist_ok=True)

        # Filename: uuid.json (avoids collisions)
        file_id = str(uuid.uuid4())
        file_path = dir_path / f"{file_id}.json"

        # Write payload + archival metadata
        archive_record = {
            "archive_id": file_id,
            "provider": provider,
            "archived_at": ts.isoformat(),
            "payload": payload,
        }

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(archive_record, f, default=str, ensure_ascii=False)

        size = file_path.stat().st_size
        log.debug("payload_archived",
                  provider=provider,
                  path=str(file_path),
                  size_bytes=size)

        return ArchivedFile(
            path=str(file_path),
            provider=provider,
            size_bytes=size,
            archived_at=ts,
        )

    def read(self, path: str | Path) -> dict:
        """Read an archived payload back from disk."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Archived file not found: {path}")
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def list_provider_hour(
        self,
        provider: str,
        year: int,
        month: int,
        day: int,
        hour: int,
    ) -> list[Path]:
        """List all archived files for a provider in a specific hour."""
        dir_path = self._base_path / provider / f"{year:04d}/{month:02d}/{day:02d}/{hour:02d}"
        if not dir_path.exists():
            return []
        return sorted(dir_path.glob("*.json"))

    def list_provider_day(
        self,
        provider: str,
        year: int,
        month: int,
        day: int,
    ) -> list[Path]:
        """List all archived files for a provider on a specific day."""
        dir_path = self._base_path / provider / f"{year:04d}/{month:02d}/{day:02d}"
        if not dir_path.exists():
            return []
        return sorted(dir_path.glob("**/*.json"))

    def storage_stats(self) -> dict:
        """Return storage statistics."""
        total_files = 0
        total_bytes = 0
        per_provider = {}

        for provider_dir in self._base_path.iterdir():
            if not provider_dir.is_dir():
                continue
            provider_files = list(provider_dir.rglob("*.json"))
            provider_bytes = sum(f.stat().st_size for f in provider_files)
            per_provider[provider_dir.name] = {
                "files": len(provider_files),
                "bytes": provider_bytes,
            }
            total_files += len(provider_files)
            total_bytes += provider_bytes

        return {
            "total_files": total_files,
            "total_bytes": total_bytes,
            "per_provider": per_provider,
        }
