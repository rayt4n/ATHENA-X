"""Tests for market logic validator."""
import pytest
from datetime import datetime, timezone
from athena_x_validator_market_logic import MarketLogicValidator
from athena_x_runtime_validation_types import (
    ValidationContext, ValidationStatus, ValidationReason,
)


@pytest.fixture
def validator():
    return MarketLogicValidator()


def make_context():
    return ValidationContext(
        pipelineStartedAt=datetime.now(timezone.utc),
        provider="yahoo", symbol="SPY", asset_class="etf",
    )


async def test_valid_ohlc_passes(validator):
    result = await validator.validate(
        {"open": 100, "high": 105, "low": 99, "close": 104, "volume": 1000},
        make_context(),
    )
    assert result.status == ValidationStatus.VERIFIED


async def test_high_lt_low_rejected(validator):
    result = await validator.validate(
        {"high": 99, "low": 105},  # high < low
        make_context(),
    )
    assert result.status == ValidationStatus.REJECTED
    assert result.reason == ValidationReason.HIGH_LT_LOW


async def test_close_gt_high_rejected(validator):
    result = await validator.validate(
        {"close": 110, "high": 105},
        make_context(),
    )
    assert result.status == ValidationStatus.REJECTED
    assert result.reason == ValidationReason.CLOSE_GT_HIGH


async def test_negative_volume_rejected(validator):
    result = await validator.validate(
        {"volume": -100},
        make_context(),
    )
    assert result.status == ValidationStatus.REJECTED
    assert result.reason == ValidationReason.NEGATIVE_VOLUME


async def test_negative_oi_rejected(validator):
    result = await validator.validate(
        {"open_interest": -50},
        make_context(),
    )
    assert result.status == ValidationStatus.REJECTED
    assert result.reason == ValidationReason.NEGATIVE_OI


async def test_iv_too_high_rejected(validator):
    result = await validator.validate(
        {"iv": 15.0},  # 1500%
        make_context(),
    )
    assert result.status == ValidationStatus.REJECTED
    assert result.reason == ValidationReason.IV_TOO_HIGH


async def test_negative_iv_rejected(validator):
    result = await validator.validate(
        {"iv": -0.3},
        make_context(),
    )
    assert result.status == ValidationStatus.REJECTED
    assert result.reason == ValidationReason.IV_TOO_HIGH


async def test_impossible_delta_rejected(validator):
    result = await validator.validate(
        {"delta": 2.0},  # delta must be |delta| <= 1
        make_context(),
    )
    assert result.status == ValidationStatus.REJECTED
    assert result.reason == ValidationReason.IMPOSSIBLE_GREEK


async def test_negative_gamma_rejected(validator):
    result = await validator.validate(
        {"gamma": -0.5},
        make_context(),
    )
    assert result.status == ValidationStatus.REJECTED
    assert result.reason == ValidationReason.IMPOSSIBLE_GREEK


async def test_valid_greeks_pass(validator):
    result = await validator.validate(
        {"delta": 0.5, "gamma": 0.02, "theta": -5.0, "vega": 0.1},
        make_context(),
    )
    assert result.status == ValidationStatus.VERIFIED
