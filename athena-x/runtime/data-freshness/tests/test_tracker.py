"""Tests for freshness tracker (Stage 2 req 1.9)."""
import pytest
from datetime import datetime, timezone, timedelta
from athena_x_runtime_data_freshness import FreshnessTracker, FreshnessStatus


def test_register_stream():
    tracker = FreshnessTracker()
    tracker.register_stream("yahoo:NVDA", expected_frequency_s=1.0)
    streams = tracker.list_all_streams()
    assert len(streams) == 1
    assert streams[0].stream_id == "yahoo:NVDA"


def test_unregistered_stream_returns_no_data():
    tracker = FreshnessTracker()
    assert tracker.get_status("unknown") == FreshnessStatus.NO_DATA


def test_fresh_status():
    """Stream that just received data is fresh."""
    tracker = FreshnessTracker()
    tracker.register_stream("yahoo:NVDA", expected_frequency_s=1.0)
    tracker.record_receipt("yahoo:NVDA")
    assert tracker.get_status("yahoo:NVDA") == FreshnessStatus.FRESH


def test_delayed_status():
    """Stream that hasn't received data in 1.5-3× expected is delayed."""
    tracker = FreshnessTracker()
    tracker.register_stream("yahoo:NVDA", expected_frequency_s=1.0)
    # Last received 2 seconds ago (2× expected, between 1.5× and 3×)
    old_time = datetime.now(timezone.utc) - timedelta(seconds=2)
    tracker.record_receipt("yahoo:NVDA", timestamp=old_time)
    assert tracker.get_status("yahoo:NVDA") == FreshnessStatus.DELAYED


def test_stale_status():
    """Stream that hasn't received data in >3× expected is stale."""
    tracker = FreshnessTracker()
    tracker.register_stream("yahoo:NVDA", expected_frequency_s=1.0)
    old_time = datetime.now(timezone.utc) - timedelta(seconds=5)
    tracker.record_receipt("yahoo:NVDA", timestamp=old_time)
    assert tracker.get_status("yahoo:NVDA") == FreshnessStatus.STALE


def test_actual_frequency_computed():
    """Tracker computes actual update frequency from rolling avg."""
    tracker = FreshnessTracker()
    tracker.register_stream("yahoo:NVDA", expected_frequency_s=1.0)

    # Record 3 receipts at 1-second intervals
    base = datetime.now(timezone.utc)
    tracker.record_receipt("yahoo:NVDA", timestamp=base)
    tracker.record_receipt("yahoo:NVDA", timestamp=base + timedelta(seconds=1))
    tracker.record_receipt("yahoo:NVDA", timestamp=base + timedelta(seconds=2))

    stats = tracker.get_stats("yahoo:NVDA")
    assert stats is not None
    assert stats.total_received == 3
    assert stats.actual_frequency_s is not None
    assert 0.9 < stats.actual_frequency_s < 1.1


def test_list_stale_streams():
    """list_stale_streams returns only stale streams."""
    tracker = FreshnessTracker()
    tracker.register_stream("fresh:NVDA", expected_frequency_s=1.0)
    tracker.register_stream("stale:NVDA", expected_frequency_s=1.0)

    tracker.record_receipt("fresh:NVDA")
    tracker.record_receipt("stale:NVDA",
                            timestamp=datetime.now(timezone.utc) - timedelta(seconds=10))

    stale = tracker.list_stale_streams()
    assert len(stale) == 1
    assert stale[0].stream_id == "stale:NVDA"


def test_no_data_status_initially():
    """Stream registered but never received data has NO_DATA status."""
    tracker = FreshnessTracker()
    tracker.register_stream("yahoo:NVDA", expected_frequency_s=1.0)
    assert tracker.get_status("yahoo:NVDA") == FreshnessStatus.NO_DATA


def test_multiple_streams_independent():
    """Each stream is tracked independently."""
    tracker = FreshnessTracker()
    tracker.register_stream("yahoo:NVDA", expected_frequency_s=1.0)
    tracker.register_stream("yahoo:SPY", expected_frequency_s=5.0)

    tracker.record_receipt("yahoo:NVDA")
    # SPY never received data
    assert tracker.get_status("yahoo:NVDA") == FreshnessStatus.FRESH
    assert tracker.get_status("yahoo:SPY") == FreshnessStatus.NO_DATA


def test_different_expected_frequencies():
    """Different instruments have different expected frequencies."""
    tracker = FreshnessTracker()
    tracker.register_stream("yahoo:ES", expected_frequency_s=1.0)   # 1 second
    tracker.register_stream("yahoo:VIX", expected_frequency_s=15.0)  # 15 seconds

    # 5 seconds since last update
    five_ago = datetime.now(timezone.utc) - timedelta(seconds=5)

    tracker.record_receipt("yahoo:ES", timestamp=five_ago)
    tracker.record_receipt("yahoo:VIX", timestamp=five_ago)

    # ES expected 1s, so 5s = 5× expected → stale
    assert tracker.get_status("yahoo:ES") == FreshnessStatus.STALE
    # VIX expected 15s, so 5s = 0.33× expected → fresh
    assert tracker.get_status("yahoo:VIX") == FreshnessStatus.FRESH
