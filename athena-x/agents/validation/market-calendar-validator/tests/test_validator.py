"""Tests for market calendar validator."""
import pytest
from datetime import datetime, timezone
import pytz
from athena_x_validator_market_calendar import MarketCalendarValidator
from athena_x_runtime_validation_types import (
    ValidationContext, ValidationStatus, ValidationReason,
)


@pytest.fixture
def validator():
    return MarketCalendarValidator()


def make_context(symbol="SPY"):
    return ValidationContext(
        pipelineStartedAt=datetime.now(timezone.utc),
        provider="yahoo", symbol=symbol, asset_class="etf",
    )


def et_time(month, day, hour, year=2026):
    """ET-localized datetime."""
    return pytz.timezone("America/New_York").localize(datetime(year, month, day, hour, 0))


async def test_christmas_rejected(validator):
    """SPY trading on Christmas Day is rejected."""
    ts = et_time(12, 25, 10, 2026)
    result = await validator.validate(
        {"timestamp": ts.isoformat()},
        make_context("SPY"),
    )
    assert result.status == ValidationStatus.REJECTED
    assert result.reason == ValidationReason.HOLIDAY


async def test_weekend_rejected(validator):
    """SPY trading on Saturday is rejected."""
    ts = et_time(7, 18, 10, 2026)  # Saturday
    result = await validator.validate(
        {"timestamp": ts.isoformat()},
        make_context("SPY"),
    )
    assert result.status == ValidationStatus.REJECTED
    assert result.reason == ValidationReason.WEEKEND


async def test_regular_session_accepted(validator):
    """SPY during regular trading hours is accepted."""
    ts = et_time(7, 17, 10, 2026)  # Friday 10am ET
    result = await validator.validate(
        {"timestamp": ts.isoformat()},
        make_context("SPY"),
    )
    assert result.status == ValidationStatus.VERIFIED


async def test_crypto_accepted_on_weekend(validator):
    """BTC trades 24/7 — accepted on weekend."""
    ts = et_time(7, 18, 10, 2026)  # Saturday
    result = await validator.validate(
        {"timestamp": ts.isoformat()},
        make_context("BTC-USD"),
    )
    assert result.status == ValidationStatus.VERIFIED


async def test_overnight_session_warning(validator):
    """Overnight session gets a warning (low liquidity)."""
    # Use Thursday 22:00 ET (overnight, not weekend)
    ts = et_time(7, 16, 22, 2026)  # Thursday 10pm ET
    result = await validator.validate(
        {"timestamp": ts.isoformat()},
        make_context("SPY"),
    )
    assert result.status == ValidationStatus.WARNING
    assert result.reason == ValidationReason.WRONG_SESSION


async def test_july_4_rejected(validator):
    """July 4 (Independence Day) is rejected."""
    ts = et_time(7, 4, 10, 2025)  # Friday July 4, 2025
    result = await validator.validate(
        {"timestamp": ts.isoformat()},
        make_context("SPY"),
    )
    assert result.status == ValidationStatus.REJECTED
    assert result.reason == ValidationReason.HOLIDAY
