"""Tests for schema validator."""
import pytest
from datetime import datetime, timezone
from athena_x_validator_schema import SchemaValidator
from athena_x_runtime_validation_types import (
    ValidationContext, ValidationStatus, ValidationReason,
)


@pytest.fixture
def context():
    return ValidationContext(
        pipelineStartedAt=datetime.now(timezone.utc),
        provider="yahoo", symbol="SPY", asset_class="etf",
    )


@pytest.fixture
def validator():
    return SchemaValidator()


async def test_valid_record_passes(validator, context):
    result = await validator.validate(
        {"symbol": "SPY", "last": 450.0, "timestamp": "2026-07-17T10:00:00Z"},
        context,
    )
    assert result.status == ValidationStatus.VERIFIED


async def test_missing_required_field_rejected(validator, context):
    result = await validator.validate(
        {"symbol": "SPY", "timestamp": "2026-07-17T10:00:00Z"},  # missing 'last'
        context,
    )
    assert result.status == ValidationStatus.REJECTED
    assert result.reason == ValidationReason.MISSING_REQUIRED_FIELD


async def test_null_value_rejected(validator, context):
    result = await validator.validate(
        {"symbol": "SPY", "last": None, "timestamp": "2026-07-17T10:00:00Z"},
        context,
    )
    assert result.status == ValidationStatus.REJECTED
    assert result.reason == ValidationReason.NULL_VALUE


async def test_invalid_data_type_rejected(validator, context):
    result = await validator.validate(
        {"symbol": "SPY", "last": "four hundred", "timestamp": "2026-07-17T10:00:00Z"},
        context,
    )
    assert result.status == ValidationStatus.REJECTED
    assert result.reason == ValidationReason.INVALID_DATA_TYPE


async def test_invalid_symbol_rejected(validator, context):
    result = await validator.validate(
        {"symbol": "invalid symbol with spaces", "last": 100, "timestamp": "2026-07-17T10:00:00Z"},
        context,
    )
    assert result.status == ValidationStatus.REJECTED
    assert result.reason == ValidationReason.INVALID_SYMBOL


async def test_negative_price_rejected(validator, context):
    result = await validator.validate(
        {"symbol": "SPY", "last": -100, "timestamp": "2026-07-17T10:00:00Z"},
        context,
    )
    assert result.status == ValidationStatus.REJECTED
    assert result.reason == ValidationReason.INVALID_PRECISION


async def test_special_symbols_accepted(validator, context):
    """Special symbols like BTC-USD, Gold, Oil are accepted."""
    for sym in ["BTC-USD", "ETH-USD", "Gold", "Oil", "Copper", "USDJPY", "DXY"]:
        ctx = ValidationContext(
            pipelineStartedAt=datetime.now(timezone.utc),
            provider="yahoo", symbol=sym, asset_class="crypto",
        )
        result = await validator.validate(
            {"symbol": sym, "last": 100, "timestamp": "2026-07-17T10:00:00Z"},
            ctx,
        )
        assert result.status == ValidationStatus.VERIFIED, f"Failed for {sym}"


async def test_non_dict_record_rejected(validator, context):
    result = await validator.validate("not a dict", context)
    assert result.status == ValidationStatus.REJECTED


async def test_brk_b_symbol_accepted(validator, context):
    """BRK.B (Berkshire Hathaway) is a valid symbol."""
    result = await validator.validate(
        {"symbol": "BRK.B", "last": 400, "timestamp": "2026-07-17T10:00:00Z"},
        context,
    )
    assert result.status == ValidationStatus.VERIFIED
