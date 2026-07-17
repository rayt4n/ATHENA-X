"""Tests for market calendars (Stage 4 req 5)."""
import pytest
from athena_x_runtime_market_calendars import (
    NYSE_CALENDAR, NASDAQ_CALENDAR, CME_CALENDAR, CBOE_CALENDAR,
    FX_CALENDAR, CRYPTO_CALENDAR,
    get_calendar, list_calendars, CALENDARS,
)


def test_6_calendars_defined():
    """All 6 calendars are defined."""
    assert len(CALENDARS) == 6
    names = list_calendars()
    for expected in ["NYSE", "NASDAQ", "CME", "CBOE", "FX", "Crypto"]:
        assert expected in names


def test_nyse_regular_hours():
    """NYSE regular hours are 09:30-16:00 ET."""
    assert NYSE_CALENDAR.regular_open.hour == 9
    assert NYSE_CALENDAR.regular_open.minute == 30
    assert NYSE_CALENDAR.regular_close.hour == 16
    assert NYSE_CALENDAR.timezone == "America/New_York"


def test_nyse_has_pre_and_post_market():
    """NYSE has pre-market (04:00) and post-market (20:00)."""
    assert NYSE_CALENDAR.pre_market_open is not None
    assert NYSE_CALENDAR.pre_market_open.hour == 4
    assert NYSE_CALENDAR.post_market_close is not None
    assert NYSE_CALENDAR.post_market_close.hour == 20


def test_crypto_is_24_7():
    """Crypto trades 24/7."""
    assert CRYPTO_CALENDAR.is_24_7 is True
    assert len(CRYPTO_CALENDAR.trading_days) == 7  # every day
    assert CRYPTO_CALENDAR.timezone == "UTC"


def test_fx_is_24_5():
    """FX trades 24/5."""
    assert FX_CALENDAR.is_24_5 is True
    assert len(FX_CALENDAR.trading_days) == 5  # Mon-Fri


def test_cme_timezone_is_chicago():
    """CME is in Chicago timezone."""
    assert CME_CALENDAR.timezone == "America/Chicago"


def test_get_calendar_by_name():
    cal = get_calendar("NYSE")
    assert cal is not None
    assert cal.name == "NYSE"


def test_get_unknown_calendar_returns_none():
    assert get_calendar("UNKNOWN") is None
