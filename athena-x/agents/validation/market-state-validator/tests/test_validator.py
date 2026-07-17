"""Tests for market state validator."""
import pytest
from datetime import datetime, timezone, timedelta
from athena_x_validator_market_state import MarketStateValidator, FeedTimestamps
from athena_x_runtime_validation_types import (
    ValidationContext, ValidationStatus, ValidationReason,
)


@pytest.fixture
def validator():
    return MarketStateValidator(max_desync_seconds=5.0)


def make_context(symbol="SPY"):
    return ValidationContext(
        pipelineStartedAt=datetime.now(timezone.utc),
        provider="yahoo", symbol=symbol, asset_class="etf",
    )


def test_feed_timestamps_desync():
    """FeedTimestamps computes desync correctly."""
    now = datetime.now(timezone.utc)
    ft = FeedTimestamps(feeds={
        "SPY": now,
        "ES": now,
        "VIX": now - timedelta(seconds=2),
    })
    assert ft.desync_seconds == 2.0
    assert ft.stale_feeds == []


def test_feed_timestamps_stale_detection():
    """Feeds >5s behind max are flagged as stale."""
    now = datetime.now(timezone.utc)
    ft = FeedTimestamps(feeds={
        "SPY": now,
        "ES": now,
        "news": now - timedelta(seconds=10),  # stale
    })
    assert "news" in ft.stale_feeds
    assert "SPY" not in ft.stale_feeds


async def test_synchronized_feeds_pass(validator):
    """All feeds within tolerance pass."""
    now = datetime.now(timezone.utc)
    validator.update_feed("ES", now)
    validator.update_feed("VIX", now - timedelta(seconds=1))
    validator.update_feed("options", now)

    result = await validator.validate(
        {"timestamp": now.isoformat()},
        make_context("SPY"),
    )
    assert result.status == ValidationStatus.VERIFIED


async def test_stale_feed_warning(validator):
    """One stale feed triggers a warning."""
    now = datetime.now(timezone.utc)
    validator.update_feed("ES", now)
    validator.update_feed("VIX", now)
    validator.update_feed("news", now - timedelta(seconds=10))  # stale

    result = await validator.validate(
        {"timestamp": now.isoformat()},
        make_context("SPY"),
    )
    assert result.status == ValidationStatus.WARNING
    assert result.reason == ValidationReason.FEED_DESYNC


async def test_severe_desync_quarantine(validator):
    """Severe desynchronization (>3× threshold) triggers quarantine."""
    now = datetime.now(timezone.utc)
    validator.update_feed("ES", now)
    validator.update_feed("VIX", now)
    validator.update_feed("news", now - timedelta(seconds=30))  # 30s stale

    result = await validator.validate(
        {"timestamp": now.isoformat()},
        make_context("SPY"),
    )
    assert result.status == ValidationStatus.QUARANTINED
    assert result.reason == ValidationReason.FEED_DESYNC


async def test_single_feed_passes(validator):
    """With only one feed, desync check is skipped."""
    now = datetime.now(timezone.utc)
    result = await validator.validate(
        {"timestamp": now.isoformat()},
        make_context("SPY"),
    )
    assert result.status == ValidationStatus.VERIFIED


def test_get_state(validator):
    """get_state returns current feed state."""
    now = datetime.now(timezone.utc)
    validator.update_feed("SPY", now)
    validator.update_feed("ES", now)
    state = validator.get_state()
    assert "SPY" in state["feeds"]
    assert "ES" in state["feeds"]
    assert state["desync_seconds"] == 0.0
