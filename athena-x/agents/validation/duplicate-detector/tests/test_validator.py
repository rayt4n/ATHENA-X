"""Tests for duplicate detector."""
import pytest
from datetime import datetime, timezone
from athena_x_validator_duplicate import DuplicateDetector
from athena_x_runtime_validation_types import (
    ValidationContext, ValidationStatus, ValidationReason,
)


@pytest.fixture
def validator():
    return DuplicateDetector(cache_size=100)


def make_context(provider="yahoo", symbol="SPY"):
    return ValidationContext(
        pipelineStartedAt=datetime.now(timezone.utc),
        provider=provider, symbol=symbol, asset_class="etf",
    )


async def test_unique_record_passes(validator):
    result = await validator.validate(
        {"symbol": "SPY", "last": 450.0, "timestamp": "2026-07-17T10:00:00Z"},
        make_context(),
    )
    assert result.status == ValidationStatus.VERIFIED


async def test_duplicate_record_rejected(validator):
    """Same provider + symbol + ts + payload is rejected."""
    record = {"symbol": "SPY", "last": 450.0, "timestamp": "2026-07-17T10:00:00Z"}
    ctx = make_context()
    await validator.validate(record, ctx)
    result = await validator.validate(record, ctx)
    assert result.status == ValidationStatus.REJECTED
    assert result.reason == ValidationReason.DUPLICATE_PAYLOAD


async def test_same_payload_different_provider_accepted(validator):
    """Same payload from different providers is accepted."""
    record = {"symbol": "SPY", "last": 450.0, "timestamp": "2026-07-17T10:00:00Z"}
    await validator.validate(record, make_context(provider="yahoo"))
    result = await validator.validate(record, make_context(provider="polygon"))
    assert result.status == ValidationStatus.VERIFIED


async def test_same_payload_different_symbol_accepted(validator):
    """Same payload for different symbols is accepted."""
    record = {"symbol": "SPY", "last": 450.0, "timestamp": "2026-07-17T10:00:00Z"}
    await validator.validate(record, make_context(symbol="SPY"))
    result = await validator.validate(record, make_context(symbol="QQQ"))
    assert result.status == ValidationStatus.VERIFIED


async def test_same_payload_different_timestamp_accepted(validator):
    """Same payload with different timestamps is accepted."""
    ctx = make_context()
    await validator.validate(
        {"symbol": "SPY", "last": 450.0, "timestamp": "2026-07-17T10:00:00Z"}, ctx
    )
    result = await validator.validate(
        {"symbol": "SPY", "last": 450.0, "timestamp": "2026-07-17T10:00:01Z"}, ctx
    )
    assert result.status == ValidationStatus.VERIFIED


async def test_cache_eviction(validator):
    """Cache evicts oldest entries when full."""
    ctx = make_context()
    # Fill cache (size 100)
    for i in range(100):
        await validator.validate(
            {"symbol": "SPY", "last": 450.0 + i, "timestamp": f"2026-07-17T10:00:{i:02d}Z"},
            ctx,
        )
    stats = validator.get_stats()
    assert stats["cache_size"] == 100

    # Add one more — should evict the oldest
    await validator.validate(
        {"symbol": "SPY", "last": 999.0, "timestamp": "2026-07-17T10:30:00Z"},
        ctx,
    )
    stats = validator.get_stats()
    assert stats["cache_size"] == 100  # still 100, not 101

    # The first record should now be accepted again (evicted)
    result = await validator.validate(
        {"symbol": "SPY", "last": 450.0, "timestamp": "2026-07-17T10:00:00Z"},
        ctx,
    )
    assert result.status == ValidationStatus.VERIFIED
