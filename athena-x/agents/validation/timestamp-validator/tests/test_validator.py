"""Tests for timestamp validator."""
import pytest
from datetime import datetime, timezone, timedelta
from athena_x_validator_timestamp import TimestampValidator
from athena_x_runtime_validation_types import (
    ValidationContext, ValidationStatus, ValidationReason,
)


@pytest.fixture
def validator():
    return TimestampValidator()


def make_context(provider="yahoo", symbol="SPY"):
    return ValidationContext(
        pipelineStartedAt=datetime.now(timezone.utc),
        provider=provider, symbol=symbol, asset_class="etf",
    )


async def test_valid_timestamp_passes(validator):
    ctx = make_context()
    result = await validator.validate(
        {"timestamp": datetime.now(timezone.utc).isoformat()},
        ctx,
    )
    assert result.status == ValidationStatus.VERIFIED


async def test_naive_timestamp_rejected(validator):
    """Timestamps without timezone are rejected."""
    ctx = make_context()
    result = await validator.validate(
        {"timestamp": "2026-07-17T10:00:00"},  # no timezone
        ctx,
    )
    assert result.status == ValidationStatus.REJECTED
    assert result.reason == ValidationReason.NAIVE_TIMESTAMP


async def test_future_timestamp_rejected(validator):
    """Timestamps too far in the future are rejected."""
    ctx = make_context()
    future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    result = await validator.validate({"timestamp": future}, ctx)
    assert result.status == ValidationStatus.REJECTED
    assert result.reason == ValidationReason.FUTURE_TIMESTAMP


async def test_stale_timestamp_warning(validator):
    """Old timestamps get a warning (not rejection)."""
    ctx = make_context()
    stale = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
    result = await validator.validate({"timestamp": stale}, ctx)
    assert result.status == ValidationStatus.WARNING
    assert result.reason == ValidationReason.STALE_TIMESTAMP


async def test_out_of_order_rejected(validator):
    """Out-of-order events are rejected."""
    ctx = make_context()
    now = datetime.now(timezone.utc)
    # First event — very recent (1s ago, within clock drift tolerance)
    ts1 = (now - timedelta(seconds=1)).isoformat()
    await validator.validate({"timestamp": ts1}, ctx)
    # Second event — earlier than first, also within tolerance
    earlier = (now - timedelta(seconds=4)).isoformat()
    result = await validator.validate({"timestamp": earlier}, ctx)
    assert result.status == ValidationStatus.REJECTED
    assert result.reason == ValidationReason.OUT_OF_ORDER


async def test_duplicate_timestamp_rejected(validator):
    """Duplicate timestamps (same provider+symbol) are rejected."""
    ctx = make_context()
    ts = datetime.now(timezone.utc).isoformat()
    # First occurrence
    await validator.validate({"timestamp": ts}, ctx)
    # Duplicate
    result = await validator.validate({"timestamp": ts}, ctx)
    assert result.status == ValidationStatus.REJECTED
    assert result.reason == ValidationReason.DUPLICATE_TIMESTAMP


async def test_duplicate_different_provider_accepted(validator):
    """Same timestamp from different providers is accepted."""
    ts = datetime.now(timezone.utc).isoformat()
    await validator.validate({"timestamp": ts}, make_context(provider="yahoo"))
    result = await validator.validate({"timestamp": ts}, make_context(provider="polygon"))
    assert result.status == ValidationStatus.VERIFIED


async def test_unix_millis_timestamp_accepted(validator):
    """Unix millisecond timestamps are parsed correctly."""
    ctx = make_context()
    ts_millis = int(datetime.now(timezone.utc).timestamp() * 1000)
    result = await validator.validate({"timestamp": ts_millis}, ctx)
    assert result.status == ValidationStatus.VERIFIED
