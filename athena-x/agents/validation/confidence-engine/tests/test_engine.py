"""Tests for confidence engine."""
import pytest
from datetime import datetime, timezone
from athena_x_validator_confidence import ConfidenceEngine, ConfidenceFactors
from athena_x_runtime_validation_types import (
    ValidationContext, ValidationStatus,
)


@pytest.fixture
def validator():
    return ConfidenceEngine()


def make_context(provider="databento", peers=None, recent=None):
    return ValidationContext(
        pipelineStartedAt=datetime.now(timezone.utc),
        provider=provider, symbol="SPY", asset_class="etf",
        peerValues=peers or {},
        recentValues=recent or [],
    )


def test_factors_weighted_score():
    """Weighted score is 0..1 and weights sum to 1.0."""
    f = ConfidenceFactors(
        provider_reliability=1.0,
        peer_agreement=1.0,
        freshness=1.0,
        latency_score=1.0,
        completeness=1.0,
        historical_accuracy=1.0,
    )
    assert f.weighted_score == 1.0

    f2 = ConfidenceFactors(
        provider_reliability=0.5,
        peer_agreement=0.5,
        freshness=0.5,
        latency_score=0.5,
        completeness=0.5,
        historical_accuracy=0.5,
    )
    assert f2.weighted_score == 0.5


async def test_high_confidence_record(validator):
    """Databento + peers + complete record = high confidence."""
    result = await validator.validate(
        {"symbol": "SPY", "last": 450.0, "timestamp": "2026-07-17T10:00:00Z"},
        make_context(provider="databento",
                     peers={"yahoo": 450.1, "polygon": 450.0},
                     recent=[450, 450.1, 449.9, 450, 450.2]),
    )
    assert result.status == ValidationStatus.VERIFIED
    assert result.metadata["confidence_score"] >= 0.9


async def test_low_confidence_provider(validator):
    """Simulated provider (low reliability) → lower confidence."""
    result = await validator.validate(
        {"symbol": "SPY", "last": 450.0, "timestamp": "2026-07-17T10:00:00Z"},
        make_context(provider="simulated", peers={}, recent=[]),
    )
    # simulated has 0.5 reliability, no peers, no recent → lower score
    assert result.metadata["confidence_score"] < 0.9


async def test_no_peers_lower_confidence(validator):
    """Records without peer verification have lower confidence."""
    with_peers = await validator.validate(
        {"symbol": "SPY", "last": 450.0, "timestamp": "2026-07-17T10:00:00Z"},
        make_context(peers={"yahoo": 450.1, "polygon": 450.0},
                     recent=[450, 450.1, 449.9, 450, 450.2]),
    )
    without_peers = await validator.validate(
        {"symbol": "SPY", "last": 450.0, "timestamp": "2026-07-17T10:00:00Z"},
        make_context(peers={}, recent=[450, 450.1, 449.9, 450, 450.2]),
    )
    assert with_peers.metadata["confidence_score"] > without_peers.metadata["confidence_score"]


async def test_incomplete_record_lower_confidence(validator):
    """Records with missing fields have lower completeness score."""
    complete = await validator.validate(
        {"symbol": "SPY", "last": 450.0, "timestamp": "2026-07-17T10:00:00Z"},
        make_context(),
    )
    incomplete = await validator.validate(
        {"symbol": "SPY", "last": 450.0},  # missing timestamp
        make_context(),
    )
    assert complete.metadata["factors"]["completeness"] > incomplete.metadata["factors"]["completeness"]


def test_update_provider_accuracy(validator):
    """update_provider_accuracy sets the rolling accuracy."""
    validator.update_provider_accuracy("yahoo", 0.95)
    assert validator._provider_accuracy["yahoo"] == 0.95


async def test_latency_affects_confidence(validator):
    """High latency reduces confidence."""
    low_lat = await validator.validate(
        {"symbol": "SPY", "last": 450.0, "timestamp": "2026-07-17T10:00:00Z", "latency": 10},
        make_context(),
    )
    high_lat = await validator.validate(
        {"symbol": "SPY", "last": 450.0, "timestamp": "2026-07-17T10:00:00Z", "latency": 500},
        make_context(),
    )
    assert low_lat.metadata["factors"]["latency_score"] > high_lat.metadata["factors"]["latency_score"]
