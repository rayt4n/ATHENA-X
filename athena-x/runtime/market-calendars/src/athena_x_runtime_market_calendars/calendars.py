"""Market calendar configurations (Stage 4 req 5).

Support:
  - NYSE (09:30-16:00 ET, Mon-Fri)
  - NASDAQ (09:30-16:00 ET, Mon-Fri)
  - CME (varies by product — futures nearly 24h)
  - CBOE (09:30-16:00 ET for options, 03:00-09:15 for VIX futures)
  - FX (24/5)
  - Crypto (24/7)

Include: holidays, half-days, early closes, DST transitions.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import time, timedelta
import pytz


@dataclass(frozen=True)
class MarketCalendar:
    """A market calendar configuration."""
    name: str
    timezone: str
    # Regular trading hours (in local time)
    regular_open: time
    regular_close: time
    # Pre-market hours (optional)
    pre_market_open: time | None = None
    # Post-market hours (optional)
    post_market_close: time | None = None
    # Trading days per week (0=Mon, 6=Sun)
    trading_days: tuple[int, ...] = (0, 1, 2, 3, 4)  # Mon-Fri
    # 24/7 trading (crypto)
    is_24_7: bool = False
    # 24/5 trading (FX)
    is_24_5: bool = False
    # Description
    description: str = ""


# ET timezone
ET = "America/New_York"
UTC = "UTC"
CT = "America/Chicago"  # CME


NYSE_CALENDAR = MarketCalendar(
    name="NYSE",
    timezone=ET,
    regular_open=time(9, 30),
    regular_close=time(16, 0),
    pre_market_open=time(4, 0),
    post_market_close=time(20, 0),
    description="New York Stock Exchange",
)

NASDAQ_CALENDAR = MarketCalendar(
    name="NASDAQ",
    timezone=ET,
    regular_open=time(9, 30),
    regular_close=time(16, 0),
    pre_market_open=time(4, 0),
    post_market_close=time(20, 0),
    description="NASDAQ Stock Market",
)

CME_CALENDAR = MarketCalendar(
    name="CME",
    timezone=CT,
    regular_open=time(17, 0),  # 5pm CT (Sunday open)
    regular_close=time(16, 0),  # 4pm CT (Friday close)
    pre_market_open=None,
    post_market_close=None,
    trading_days=(0, 1, 2, 3, 4, 6),  # Sun-Fri
    description="Chicago Mercantile Exchange (futures)",
)

CBOE_CALENDAR = MarketCalendar(
    name="CBOE",
    timezone=ET,
    regular_open=time(9, 30),
    regular_close=time(16, 0),
    pre_market_open=time(3, 0),  # VIX futures pre-market
    post_market_close=time(20, 0),
    description="Chicago Board Options Exchange",
)

FX_CALENDAR = MarketCalendar(
    name="FX",
    timezone=UTC,
    regular_open=time(0, 0),
    regular_close=time(0, 0),  # 24h
    is_24_5=True,
    trading_days=(0, 1, 2, 3, 4),
    description="Foreign Exchange (24/5)",
)

CRYPTO_CALENDAR = MarketCalendar(
    name="Crypto",
    timezone=UTC,
    regular_open=time(0, 0),
    regular_close=time(0, 0),
    is_24_7=True,
    trading_days=(0, 1, 2, 3, 4, 5, 6),  # every day
    description="Cryptocurrency (24/7)",
)


CALENDARS: dict[str, MarketCalendar] = {
    "NYSE": NYSE_CALENDAR,
    "NASDAQ": NASDAQ_CALENDAR,
    "CME": CME_CALENDAR,
    "CBOE": CBOE_CALENDAR,
    "FX": FX_CALENDAR,
    "Crypto": CRYPTO_CALENDAR,
}


def get_calendar(name: str) -> MarketCalendar | None:
    """Get a calendar by name."""
    return CALENDARS.get(name)


def list_calendars() -> list[str]:
    """List all available calendar names."""
    return list(CALENDARS.keys())
