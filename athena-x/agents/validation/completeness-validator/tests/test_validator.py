"""Tests for completeness validator."""
import pytest
from datetime import datetime, timezone
from athena_x_validator_completeness import CompletenessValidator
from athena_x_runtime_validation_types import (
    ValidationContext, ValidationStatus, ValidationReason,
)


@pytest.fixture
def validator():
    return CompletenessValidator()


def make_context(asset_class="etf"):
    return ValidationContext(
        pipelineStartedAt=datetime.now(timezone.utc),
        provider="yahoo", symbol="SPY", asset_class=asset_class,
    )


async def test_complete_quote_passes(validator):
    result = await validator.validate(
        {"symbol": "SPY", "last": 450.0, "timestamp": "2026-07-17T10:00:00Z"},
        make_context(),
    )
    assert result.status == ValidationStatus.VERIFIED


async def test_missing_quote_field_warning(validator):
    result = await validator.validate(
        {"symbol": "SPY", "last": 450.0},  # missing timestamp
        make_context(),
    )
    assert result.status == ValidationStatus.WARNING
    assert result.reason == ValidationReason.MISSING_BAR


async def test_complete_bar_passes(validator):
    result = await validator.validate(
        {"timestamp": 1700000000000, "open": 100, "high": 105, "low": 99, "close": 104, "volume": 1000},
        make_context(),
    )
    assert result.status == ValidationStatus.VERIFIED


async def test_missing_bar_field_warning(validator):
    result = await validator.validate(
        {"open": 100, "high": 105, "low": 99, "close": 104},  # missing volume + timestamp
        make_context(),
    )
    assert result.status == ValidationStatus.WARNING


async def test_complete_option_record_passes(validator):
    record = {
        "symbol": "NVDA",
        "expiry": "2026-07-18",
        "strikes": [
            {"strike": 125, "call": {"delta": 0.7, "gamma": 0.05, "theta": -0.5, "vega": 0.1},
             "put": {"delta": -0.3, "gamma": 0.05, "theta": -0.5, "vega": 0.1}},
        ],
    }
    result = await validator.validate(record, make_context("option"))
    assert result.status == ValidationStatus.VERIFIED


async def test_missing_greeks_warning(validator):
    record = {
        "symbol": "NVDA",
        "expiry": "2026-07-18",
        "strikes": [
            {"strike": 125, "call": {"delta": 0.7},  # missing gamma, theta, vega
             "put": {"delta": -0.3}},
        ],
    }
    result = await validator.validate(record, make_context("option"))
    assert result.status == ValidationStatus.WARNING
    assert result.reason == ValidationReason.MISSING_GREEK
