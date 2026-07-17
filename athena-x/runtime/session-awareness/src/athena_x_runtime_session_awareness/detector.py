"""Trading session detector.

Classifies a timestamp into one of 6 trading sessions (Stage 2 req 1.8):
  - overnight:    20:00 – 04:00 ET (Mon-Fri)
  - pre-market:   04:00 – 09:30 ET (Mon-Fri)
  - regular:      09:30 – 16:00 ET (Mon-Fri)
  - post-market:  16:00 – 20:00 ET (Mon-Fri)
  - weekend:      Fri 20:00 – Sun 20:00 ET
  - holiday:      NYSE-observed holidays

Crypto trades 24/7 — for crypto symbols, session is always 'regular'.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Literal
import pytz

from .holidays import is_holiday


ET = pytz.timezone("America/New_York")


class SessionType(str, Enum):
    OVERNIGHT = "overnight"
    PRE_MARKET = "pre-market"
    REGULAR = "regular"
    POST_MARKET = "post-market"
    WEEKEND = "weekend"
    HOLIDAY = "holiday"


@dataclass(frozen=True)
class SessionInfo:
    """Detected trading session for a timestamp."""
    session: SessionType
    et_time: datetime  # ET-localized
    utc_time: datetime
    description: str
    is_crypto: bool = False

    def __str__(self) -> str:
        return f"{self.session.value} ({self.et_time.strftime('%H:%M %Z')})"


class SessionDetector:
    """Detects the trading session for a given timestamp.

    Usage:
        detector = SessionDetector()
        info = detector.detect(datetime.now(timezone.utc), symbol="SPY")
        print(info.session)  # 'regular' / 'pre-market' / etc.
    """

    def detect(self, timestamp: datetime, *, symbol: str = "") -> SessionInfo:
        """Detect the session for a UTC timestamp.

        Args:
            timestamp: UTC-aware datetime
            symbol: optional symbol — if it's a crypto symbol, session is always 'regular'
        """
        if timestamp.tzinfo is None:
            raise ValueError("timestamp must be timezone-aware (UTC)")

        utc_time = timestamp.astimezone(timezone.utc)
        et_time = timestamp.astimezone(ET)

        # Crypto trades 24/7
        if self._is_crypto(symbol):
            return SessionInfo(
                session=SessionType.REGULAR,
                et_time=et_time,
                utc_time=utc_time,
                description="Crypto markets trade 24/7",
                is_crypto=True,
            )

        # Check holidays first
        if is_holiday(et_time.date()):
            return SessionInfo(
                session=SessionType.HOLIDAY,
                et_time=et_time,
                utc_time=utc_time,
                description="NYSE holiday — markets closed",
            )

        weekday = et_time.weekday()  # 0=Mon, 6=Sun
        hour = et_time.hour

        # Weekend: Friday 20:00+ through Sunday 20:00
        if weekday == 4 and hour >= 20:  # Friday after 20:00
            return SessionInfo(
                session=SessionType.WEEKEND, et_time=et_time, utc_time=utc_time,
                description="Weekend (Friday after-hours)",
            )
        if weekday == 5:  # Saturday
            return SessionInfo(
                session=SessionType.WEEKEND, et_time=et_time, utc_time=utc_time,
                description="Weekend (Saturday)",
            )
        if weekday == 6 and hour < 20:  # Sunday before 20:00
            return SessionInfo(
                session=SessionType.WEEKEND, et_time=et_time, utc_time=utc_time,
                description="Weekend (Sunday)",
            )

        # Weekday sessions (ET):
        # 20:00 – 04:00 → overnight
        # 04:00 – 09:30 → pre-market
        # 09:30 – 16:00 → regular
        # 16:00 – 20:00 → post-market

        # Convert to minutes-since-midnight for easier comparison
        minutes = hour * 60 + et_time.minute

        if minutes >= 20 * 60 or minutes < 4 * 60:
            return SessionInfo(
                session=SessionType.OVERNIGHT, et_time=et_time, utc_time=utc_time,
                description="Overnight session",
            )
        if minutes < 9 * 60 + 30:
            return SessionInfo(
                session=SessionType.PRE_MARKET, et_time=et_time, utc_time=utc_time,
                description="Pre-market session",
            )
        if minutes < 16 * 60:
            return SessionInfo(
                session=SessionType.REGULAR, et_time=et_time, utc_time=utc_time,
                description="Regular Trading Hours (RTH)",
            )
        return SessionInfo(
            session=SessionType.POST_MARKET, et_time=et_time, utc_time=utc_time,
            description="Post-market session",
        )

    def _is_crypto(self, symbol: str) -> bool:
        """Detect if a symbol is a crypto pair."""
        s = symbol.upper()
        if "-" in s and any(c in s for c in ["BTC", "ETH", "SOL", "XRP", "ADA", "DOGE"]):
            return True
        if s in {"BTC", "ETH", "SOL", "XRP", "ADA", "DOGE"}:
            return True
        return False
