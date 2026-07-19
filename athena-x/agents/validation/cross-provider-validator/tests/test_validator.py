"""Tests for cross-provider validator."""
import pytest
from datetime import datetime, timezone
from athena_x_validator_cross_provider import CrossProviderValidator
from athena_x_runtime_validation_types import (
    ValidationContext, ValidationStatus, ValidationReason,
)


@pytest.fixture
def validator():
    return CrossProviderValidator(tolerance_pct=0.005)  # 0.5%


def make_context(value, peers=None, provider="yahoo"):
    return ValidationContext(
        pipelineStartedAt=datetime.now(timezone.utc),
        provider=provider, symbol="SPY", asset_class="etf",
        peerValues=peers or {},
    )


async def test_matches_consensus(validator):
    """Value close to peer consensus is verified."""
    result = await validator.validate(
        {"last": 752.45},
        make_context(752.45, {"polygon": 752.45, "finnhub": 752.46}),
    )
    assert result.status == ValidationStatus.VERIFIED


async def test_outlier_rejected(validator):
    """Value far from consensus is rejected."""
    result = await validator.validate(
        {"last": 742.00},
        make_context(742.00, {"polygon": 752.45, "finnhub": 752.46}),
    )
    assert result.status == ValidationStatus.REJECTED
    assert result.reason == ValidationReason.CONSENSUS_DISAGREEMENT


async def test_single_source_warning(validator):
    """Single provider (no peers) gets a warning."""
    result = await validator.validate(
        {"last": 752.45},
        make_context(752.45, {}),  # no peers
    )
    assert result.status == ValidationStatus.WARNING
    assert result.reason == ValidationReason.SINGLE_SOURCE


async def test_peer_outlier_warning(validator):
    """When a peer is an outlier, our value (close to consensus) is verified."""
    result = await validator.validate(
        {"last": 752.45},
        make_context(752.45, {"polygon": 752.46, "finnhub": 742.00}),  # finnhub is outlier
    )
    # Our value matches consensus (median of 752.45, 752.46, 742.00 = 752.45)
    # So we should be verified
    assert result.status == ValidationStatus.VERIFIED


async def test_value_slightly_off_with_peer_outlier_warning(validator):
    """If our value is slightly off and a peer is way off, we get a warning."""
    result = await validator.validate(
        {"last": 752.40},
        make_context(752.40, {"polygon": 752.45, "finnhub": 742.00}),  # finnhub is outlier
    )
    # Our value is closer to consensus than finnhub — so we're not the outlier
    # But we're slightly off from consensus — should be verified or warning
    assert result.status in (ValidationStatus.VERIFIED, ValidationStatus.WARNING)


async def test_no_last_field_passes(validator):
    """Records without 'last' field pass (cross-provider check is skipped)."""
    result = await validator.validate(
        {"symbol": "SPY"},
        make_context(None, {"polygon": 752.45}),
    )
    assert result.status == ValidationStatus.VERIFIED


async def test_within_tolerance_passes(validator):
    """Values within tolerance pass."""
    result = await validator.validate(
        {"last": 752.50},
        make_context(752.50, {"polygon": 752.45, "finnhub": 752.46}),
    )
    # 752.50 vs consensus 752.46 → deviation 0.005% — within tolerance
    assert result.status in (ValidationStatus.VERIFIED, ValidationStatus.WARNING)
