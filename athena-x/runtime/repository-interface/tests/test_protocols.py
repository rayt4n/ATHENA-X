"""Tests for repository interface (Stage 5 strategic req)."""
import pytest
from athena_x_runtime_repository_interface import (
    MarketRepository, OptionsRepository, NewsRepository, MacroRepository,
    WriteResult, QueryResult, RepositoryError,
)


def test_write_result_has_required_fields():
    """WriteResult has record_id, schema, table, written_at."""
    from datetime import datetime, timezone
    r = WriteResult(
        record_id="rec-123",
        schema="canonical_market",
        table="quotes",
        written_at=datetime.now(timezone.utc),
    )
    assert r.record_id == "rec-123"
    assert r.schema == "canonical_market"
    assert r.superseded_record_id is None  # no supersession by default


def test_write_result_supports_supersession():
    """WriteResult tracks when a record supersedes another (Stage 5 req 7)."""
    from datetime import datetime, timezone
    r = WriteResult(
        record_id="rec-new",
        schema="canonical_market",
        table="quotes",
        written_at=datetime.now(timezone.utc),
        superseded_record_id="rec-old",
    )
    assert r.superseded_record_id == "rec-old"


def test_query_result_has_records_and_count():
    r = QueryResult(records=[1, 2, 3], count=3)
    assert r.count == 3
    assert len(r.records) == 3


def test_repository_error_includes_repository_name():
    err = RepositoryError("canonical_market", "write failed")
    assert "canonical_market" in str(err)


def test_market_repository_is_protocol():
    """MarketRepository is a runtime-checkable Protocol."""
    assert hasattr(MarketRepository, "_is_protocol")
    assert hasattr(MarketRepository, "_is_runtime_protocol")


def test_all_4_repository_protocols_defined():
    """All 4 domain repository protocols are defined."""
    assert MarketRepository is not None
    assert OptionsRepository is not None
    assert NewsRepository is not None
    assert MacroRepository is not None


def test_market_repository_has_required_methods():
    """MarketRepository defines write_quote, read_quote, write_bar, query_bars, supersede, get_history."""
    # Check protocol has these methods
    assert hasattr(MarketRepository, "write_quote")
    assert hasattr(MarketRepository, "read_quote")
    assert hasattr(MarketRepository, "write_bar")
    assert hasattr(MarketRepository, "query_bars")
    assert hasattr(MarketRepository, "supersede")
    assert hasattr(MarketRepository, "get_history")
