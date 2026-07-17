"""Tests for session detector (Stage 2 req 1.8)."""
import pytest
from datetime import datetime, timezone, timedelta
import pytz

from athena_x_runtime_session_awareness import SessionDetector, is_holiday
from athena_x_runtime_session_awareness.detector import SessionType, ET


ET_TZ = pytz.timezone("America/New_York")


def et_time(month, day, hour, minute=0, year=2026):
    """Create an ET-localized datetime."""
    return ET_TZ.localize(datetime(year, month, day, hour, minute))


def test_regular_session():
    """09:30 – 16:00 ET on a weekday is 'regular'."""
    d = SessionDetector()
    info = d.detect(et_time(7, 17, 10, 30))  # Friday 10:30 ET
    assert info.session == SessionType.REGULAR


def test_pre_market_session():
    """04:00 – 09:30 ET on a weekday is 'pre-market'."""
    d = SessionDetector()
    info = d.detect(et_time(7, 17, 7, 0))  # Friday 07:00 ET
    assert info.session == SessionType.PRE_MARKET


def test_post_market_session():
    """16:00 – 20:00 ET on a weekday is 'post-market'."""
    d = SessionDetector()
    info = d.detect(et_time(7, 17, 17, 0))  # Friday 17:00 ET
    assert info.session == SessionType.POST_MARKET


def test_overnight_session_late():
    """20:00+ on a weekday is 'overnight'."""
    d = SessionDetector()
    info = d.detect(et_time(7, 16, 21, 0))  # Thursday 21:00 ET
    assert info.session == SessionType.OVERNIGHT


def test_overnight_session_early():
    """Before 04:00 on a weekday is 'overnight'."""
    d = SessionDetector()
    info = d.detect(et_time(7, 17, 3, 0))  # Friday 03:00 ET
    assert info.session == SessionType.OVERNIGHT


def test_weekend_saturday():
    """Saturday is weekend."""
    d = SessionDetector()
    info = d.detect(et_time(7, 18, 12, 0))  # Saturday noon
    assert info.session == SessionType.WEEKEND


def test_weekend_sunday_before_8pm():
    """Sunday before 20:00 is weekend."""
    d = SessionDetector()
    info = d.detect(et_time(7, 19, 12, 0))  # Sunday noon
    assert info.session == SessionType.WEEKEND


def test_weekend_friday_after_8pm():
    """Friday after 20:00 is weekend."""
    d = SessionDetector()
    info = d.detect(et_time(7, 17, 21, 0))  # Friday 21:00 ET
    assert info.session == SessionType.WEEKEND


def test_holiday_christmas():
    """Christmas is a holiday."""
    d = SessionDetector()
    info = d.detect(et_time(12, 25, 10, 0))  # Christmas 10:00 ET
    assert info.session == SessionType.HOLIDAY


def test_holiday_july_4():
    """July 4 is a holiday (when not on a weekend)."""
    d = SessionDetector()
    # 2026-07-04 is a Saturday, so weekend check fires first.
    # Use 2025-07-04 (Friday) instead.
    info = d.detect(et_time(7, 4, 10, 0, year=2025))
    assert info.session == SessionType.HOLIDAY


def test_crypto_always_regular():
    """Crypto symbols trade 24/7 — always 'regular'."""
    d = SessionDetector()
    # Saturday at midnight — would normally be weekend
    info = d.detect(et_time(7, 18, 0, 0), symbol="BTC-USD")
    assert info.session == SessionType.REGULAR
    assert info.is_crypto is True


def test_crypto_eth():
    d = SessionDetector()
    info = d.detect(et_time(12, 25, 0, 0), symbol="ETH-USD")
    assert info.session == SessionType.REGULAR
    assert info.is_crypto is True


def test_utc_input_accepted():
    """Detector accepts UTC timestamps and converts to ET internally."""
    d = SessionDetector()
    # 2026-07-17 14:30 UTC = 10:30 ET (regular session)
    utc = datetime(2026, 7, 17, 14, 30, tzinfo=timezone.utc)
    info = d.detect(utc, symbol="SPY")
    assert info.session == SessionType.REGULAR
    assert info.utc_time == utc


def test_naive_timestamp_rejected():
    """Naive timestamps are rejected."""
    d = SessionDetector()
    with pytest.raises(ValueError):
        d.detect(datetime(2026, 7, 17, 10, 30), symbol="SPY")


def test_is_holiday():
    assert is_holiday(__import__("datetime").date(2026, 12, 25)) is True
    assert is_holiday(__import__("datetime").date(2026, 7, 17)) is False


def test_session_info_has_description():
    d = SessionDetector()
    info = d.detect(et_time(7, 17, 10, 30))
    assert isinstance(info.description, str)
    assert len(info.description) > 0


def test_session_info_str():
    d = SessionDetector()
    info = d.detect(et_time(7, 17, 10, 30))
    s = str(info)
    assert "regular" in s
