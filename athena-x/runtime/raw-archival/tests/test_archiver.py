"""Tests for raw archival (Stage 2 req 1.6)."""
import json
import pytest
from datetime import datetime, timezone
from pathlib import Path
from athena_x_runtime_raw_archival import RawArchiver


def test_archive_creates_file_with_correct_structure(tmp_path):
    """Archived files are stored under provider/yyyy/mm/dd/hh/."""
    archiver = RawArchiver(base_path=tmp_path)
    ts = datetime(2026, 7, 17, 13, 45, tzinfo=timezone.utc)

    result = archiver.archive(
        provider="yahoo",
        payload={"symbol": "NVDA", "last": 128.45},
        timestamp=ts,
    )

    # Path should be: tmp_path/yahoo/2026/07/17/13/<uuid>.json
    expected_dir = tmp_path / "yahoo" / "2026" / "07" / "17" / "13"
    assert expected_dir.exists()
    archived_files = list(expected_dir.glob("*.json"))
    assert len(archived_files) == 1
    assert result.path == str(archived_files[0])


def test_archive_preserves_payload(tmp_path):
    """Archived payload can be read back exactly as written."""
    archiver = RawArchiver(base_path=tmp_path)
    payload = {"symbol": "SPY", "last": 456.78, "bid": 456.76, "ask": 456.80}

    result = archiver.archive(provider="finnhub", payload=payload)
    read_back = archiver.read(result.path)

    assert read_back["payload"] == payload
    assert read_back["provider"] == "finnhub"
    assert "archived_at" in read_back
    assert "archive_id" in read_back


def test_archive_default_timestamp_is_now(tmp_path):
    """If no timestamp provided, uses current UTC time."""
    archiver = RawArchiver(base_path=tmp_path)
    before = datetime.now(timezone.utc)
    result = archiver.archive(provider="yahoo", payload={"x": 1})
    after = datetime.now(timezone.utc)

    assert before <= result.archived_at <= after


def test_multiple_payloads_get_unique_filenames(tmp_path):
    """Multiple payloads archived in the same hour get unique filenames."""
    archiver = RawArchiver(base_path=tmp_path)
    ts = datetime(2026, 7, 17, 13, 45, tzinfo=timezone.utc)

    paths = set()
    for i in range(10):
        r = archiver.archive(provider="yahoo", payload={"i": i}, timestamp=ts)
        paths.add(r.path)

    assert len(paths) == 10  # all unique


def test_list_provider_hour(tmp_path):
    """list_provider_hour returns all files for a specific hour."""
    archiver = RawArchiver(base_path=tmp_path)
    ts = datetime(2026, 7, 17, 13, 45, tzinfo=timezone.utc)

    for i in range(3):
        archiver.archive(provider="yahoo", payload={"i": i}, timestamp=ts)
    # Different hour
    archiver.archive(
        provider="yahoo", payload={"i": 99},
        timestamp=datetime(2026, 7, 17, 14, 0, tzinfo=timezone.utc),
    )

    files = archiver.list_provider_hour("yahoo", 2026, 7, 17, 13)
    assert len(files) == 3


def test_list_provider_day(tmp_path):
    """list_provider_day returns all files across all hours of a day."""
    archiver = RawArchiver(base_path=tmp_path)
    for hour in range(5):
        archiver.archive(
            provider="yahoo", payload={"h": hour},
            timestamp=datetime(2026, 7, 17, hour, 0, tzinfo=timezone.utc),
        )

    files = archiver.list_provider_day("yahoo", 2026, 7, 17)
    assert len(files) == 5


def test_storage_stats(tmp_path):
    """storage_stats returns aggregate counts and bytes per provider."""
    archiver = RawArchiver(base_path=tmp_path)
    for i in range(5):
        archiver.archive(provider="yahoo", payload={"i": i})
    for i in range(3):
        archiver.archive(provider="finnhub", payload={"i": i})

    stats = archiver.storage_stats()
    assert stats["total_files"] == 8
    assert stats["total_bytes"] > 0
    assert stats["per_provider"]["yahoo"]["files"] == 5
    assert stats["per_provider"]["finnhub"]["files"] == 3


def test_archive_handles_non_serializable_payload(tmp_path):
    """Archiver uses default=str to handle non-JSON-serializable values."""
    archiver = RawArchiver(base_path=tmp_path)
    # datetime is not natively JSON-serializable
    payload = {"timestamp": datetime(2026, 7, 17, tzinfo=timezone.utc)}

    result = archiver.archive(provider="yahoo", payload=payload)
    read_back = archiver.read(result.path)
    # datetime should be converted to ISO string
    assert "2026-07-17" in read_back["payload"]["timestamp"]


def test_read_nonexistent_raises(tmp_path):
    archiver = RawArchiver(base_path=tmp_path)
    with pytest.raises(FileNotFoundError):
        archiver.read(tmp_path / "nonexistent.json")
