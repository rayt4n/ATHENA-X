"""Tests for outlier detector."""
import pytest
from datetime import datetime, timezone
from athena_x_validator_outlier import OutlierDetector
from athena_x_runtime_validation_types import (
    ValidationContext, ValidationStatus, ValidationReason,
)


@pytest.fixture
def validator():
    return OutlierDetector()


def make_context(recent_values=None):
    return ValidationContext(
        pipelineStartedAt=datetime.now(timezone.utc),
        provider="yahoo", symbol="SPY", asset_class="etf",
        recentValues=recent_values or [],
    )


async def test_insufficient_samples_passes(validator):
    """With <5 recent values, outlier check is skipped."""
    result = await validator.validate(
        {"last": 999.0},
        make_context(recent_values=[100, 101, 102]),  # only 3
    )
    assert result.status == ValidationStatus.VERIFIED


async def test_normal_value_passes(validator):
    """Value close to recent median passes."""
    recent = [100, 101, 99, 100, 102, 101, 100]
    result = await validator.validate(
        {"last": 100.5},
        make_context(recent_values=recent),
    )
    assert result.status == ValidationStatus.VERIFIED


async def test_mad_outlier_quarantined(validator):
    """Value far from median (in MAD terms) is quarantined."""
    recent = [100, 101, 99, 100, 102, 101, 100, 99, 100, 101]
    result = await validator.validate(
        {"last": 150.0},  # way off
        make_context(recent_values=recent),
    )
    assert result.status == ValidationStatus.QUARANTINED
    assert result.reason in (ValidationReason.STATISTICAL_OUTLIER, ValidationReason.CIRCUIT_BREAKER)


async def test_circuit_breaker_quarantined(validator):
    """Extreme deviation (>20%) triggers circuit breaker."""
    recent = [100, 101, 99, 100, 102, 101, 100, 99, 100, 101]
    result = await validator.validate(
        {"last": 200.0},  # 100% deviation
        make_context(recent_values=recent),
    )
    assert result.status == ValidationStatus.QUARANTINED
    assert result.reason == ValidationReason.CIRCUIT_BREAKER


async def test_small_deviation_warning(validator):
    """Small deviation (5-20%) gets a warning, not quarantine."""
    recent = [100, 100, 100, 100, 100, 100, 100, 100, 100, 100]
    result = await validator.validate(
        {"last": 107.0},  # 7% deviation
        make_context(recent_values=recent),
    )
    # MAD = 0 here, so MAD check skipped. Z-score also 0 stdev. Falls to pct.
    # 7% > 5% threshold → warning
    assert result.status == ValidationStatus.WARNING


async def test_outlier_quarantined_not_rejected(validator):
    """Outliers are quarantined, not rejected (so pipeline can continue)."""
    recent = [100, 101, 99, 100, 102, 101, 100]
    result = await validator.validate(
        {"last": 150.0},
        make_context(recent_values=recent),
    )
    # Quarantined, not rejected
    assert result.status == ValidationStatus.QUARANTINED
    assert result.status != ValidationStatus.REJECTED


async def test_no_last_field_passes(validator):
    """Records without 'last' field pass."""
    result = await validator.validate(
        {"symbol": "SPY"},
        make_context(recent_values=[100, 101, 99, 100, 102]),
    )
    assert result.status == ValidationStatus.VERIFIED
