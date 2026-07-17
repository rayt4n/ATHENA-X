#!/usr/bin/env python3
"""
STEP 4 Stage 2 — Data Collection AI (Part 1: Foundation)
=========================================================
Implements:
  1. runtime/institutional-metadata/ — 10 mandatory metadata fields per record
  2. runtime/session-awareness/      — trading session detection
  3. runtime/raw-archival/           — filesystem archival (provider/yyyy/mm/dd/hh/)
  4. runtime/data-freshness/         — fresh/delayed/stale status tracking
  5. providers/base/                 — MarketDataProvider protocol (real)
  6. providers/simulated/            — dev-only simulated provider
  7. providers/yahoo/                — Yahoo Finance adapter (real, working)
  8. providers/finnhub/              — Finnhub adapter (real)
  9. providers/cnn/                  — CNN Fear & Greed + news (real)

Run: python /home/z/my-project/scripts/stage2_implement_part1.py
"""

from pathlib import Path
import textwrap

ROOT = Path("/home/z/my-project/athena-x")
ROOT.mkdir(parents=True, exist_ok=True)

FILES = []

def w(rel: str, content: str) -> None:
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(textwrap.dedent(content).lstrip("\n"))
    FILES.append(rel)


# ============================================================================
# 1. INSTITUTIONAL METADATA — runtime/institutional-metadata/
# ============================================================================

w("runtime/institutional-metadata/pyproject.toml", '''
[project]
name = "athena-x-runtime-institutional-metadata"
version = "0.1.0"
description = "10 mandatory institutional metadata fields per data record (Stage 2 req 1.5)"
requires-python = ">=3.11"
dependencies = [
    "pydantic>=2.9.0",
    "athena-x-runtime-logger",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/athena_x_runtime_institutional_metadata"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
''')

w("runtime/institutional-metadata/src/athena_x_runtime_institutional_metadata/__init__.py", '''
"""ATHENA-X institutional metadata."""
from .types import (
    InstitutionalMetadata,
    DataStatus,
    AssetClass,
    TradingSession,
    ProviderDefaults,
)
from .factory import create_metadata

__all__ = [
    "InstitutionalMetadata",
    "DataStatus",
    "AssetClass",
    "TradingSession",
    "ProviderDefaults",
    "create_metadata",
]
__version__ = "0.1.0"
''')

w("runtime/institutional-metadata/src/athena_x_runtime_institutional_metadata/types.py", '''
"""
Institutional metadata — 10 mandatory fields per data record (Stage 2 req 1.5).

Every record that enters ATHENA-X (quote, trade, bar, news headline, option chain,
macro indicator) MUST carry this metadata. It travels with the payload through
the bus, gets archived alongside raw data, and is queryable in databases.

This is IN ADDITION TO the 10 bus event metadata fields from Stage 1.
"""
from __future__ import annotations
from datetime import datetime, timezone
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field, field_validator


class DataStatus(str, Enum):
    """Freshness status of a data record."""
    FRESH = "fresh"
    DELAYED = "delayed"
    STALE = "stale"
    FAILED = "failed"


class AssetClass(str, Enum):
    EQUITY = "equity"
    ETF = "etf"
    INDEX = "index"
    FUTURE = "future"
    OPTION = "option"
    CURRENCY = "currency"
    COMMODITY = "commodity"
    YIELD = "yield"
    VOLATILITY = "volatility"
    CRYPTO = "crypto"


class TradingSession(str, Enum):
    OVERNIGHT = "overnight"
    PRE_MARKET = "pre-market"
    REGULAR = "regular"
    POST_MARKET = "post-market"
    WEEKEND = "weekend"
    HOLIDAY = "holiday"


# Default confidence scores per provider (Stage 2 req 1.5: "initially provider default")
PROVIDER_DEFAULTS = {
    "databento":       0.98,  # institutional-grade, PIT-validated
    "polygon":         0.95,
    "finnhub":         0.93,
    "flashalpha":      0.92,
    "fred":            0.97,  # official US government data
    "alphavantage":    0.88,
    "trading-economics": 0.94,
    "yahoo":           0.85,
    "reuters":         0.95,
    "wsj":             0.93,
    "cnbc":            0.90,
    "cnn":             0.88,
    "sec":             0.99,  # regulatory filings, authoritative
    "polymarket":      0.85,
    "simulated":       0.50,  # dev only — never in production
}


class ProviderDefaults:
    """Lookup for default confidence scores per provider."""
    DEFAULTS = PROVIDER_DEFAULTS

    @classmethod
    def get_confidence(cls, provider: str) -> float:
        return cls.DEFAULTS.get(provider, 0.80)


class InstitutionalMetadata(BaseModel):
    """
    The 10 mandatory institutional metadata fields (Stage 2 req 1.5).

    Every data record carries this. Bus events wrap it alongside the Stage 1
    BusEventMeta (eventId, eventType, timestamp, etc.).
    """

    model_config = ConfigDict(populate_by_name=True, use_enum_values=True)

    # 1. Provider slug
    provider: str = Field(min_length=1, description="Source provider slug")

    # 2. Provider latency (ms)
    provider_latency: int = Field(ge=0, description="ms from request to response",
                                   alias="providerLatency")

    # 3. Download timestamp (when ATHENA-X received it)
    download_timestamp: datetime = Field(description="When ATHENA-X received it",
                                          alias="downloadTimestamp")

    # 4. Market timestamp (when the market event occurred)
    market_timestamp: datetime = Field(description="When the market event occurred",
                                        alias="marketTimestamp")

    # 5. Original timezone
    timezone: str = Field(default="UTC", description="Original timezone")

    # 6. Normalized symbol
    symbol: str = Field(min_length=1, description="Normalized symbol (e.g., 'BRK.B')")

    # 7. Asset class
    asset_class: AssetClass = Field(alias="assetClass")

    # 8. Confidence score (provider default initially)
    confidence_score: float = Field(ge=0.0, le=1.0, alias="confidenceScore",
                                     description="Initially provider default")

    # 9. Status (fresh/delayed/stale/failed)
    status: DataStatus = Field(default=DataStatus.FRESH)

    # 10. Trading session
    session: TradingSession = Field(default=TradingSession.REGULAR)

    @field_validator("download_timestamp", "market_timestamp")
    @classmethod
    def must_be_utc(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("timestamps must be timezone-aware (UTC)")
        return v.astimezone(timezone.utc)

    @field_validator("confidence_score")
    @classmethod
    def in_valid_range(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError("confidence_score must be 0..1")
        return v
''')

w("runtime/institutional-metadata/src/athena_x_runtime_institutional_metadata/factory.py", '''
"""Factory for creating InstitutionalMetadata with auto-filled fields."""
from __future__ import annotations
import time
from datetime import datetime, timezone
from typing import Any

from .types import (
    InstitutionalMetadata,
    DataStatus,
    AssetClass,
    TradingSession,
    ProviderDefaults,
)


def create_metadata(
    *,
    provider: str,
    symbol: str,
    asset_class: AssetClass | str,
    market_timestamp: datetime | None = None,
    provider_latency_ms: int = 0,
    timezone_str: str = "UTC",
    session: TradingSession | str = TradingSession.REGULAR,
    status: DataStatus | str = DataStatus.FRESH,
    confidence_score: float | None = None,
) -> InstitutionalMetadata:
    """Create InstitutionalMetadata with sensible defaults.

    If confidence_score is None, uses the provider's default.
    If market_timestamp is None, uses now (UTC).
    """
    if isinstance(asset_class, str):
        asset_class = AssetClass(asset_class)
    if isinstance(session, str):
        session = TradingSession(session)
    if isinstance(status, str):
        status = DataStatus(status)

    return InstitutionalMetadata(
        provider=provider,
        providerLatency=provider_latency_ms,
        downloadTimestamp=datetime.now(timezone.utc),
        marketTimestamp=market_timestamp or datetime.now(timezone.utc),
        timezone=timezone_str,
        symbol=symbol,
        assetClass=asset_class,
        confidenceScore=confidence_score if confidence_score is not None
                        else ProviderDefaults.get_confidence(provider),
        status=status,
        session=session,
    )
''')

w("runtime/institutional-metadata/tests/__init__.py", "")
w("runtime/institutional-metadata/tests/test_metadata.py", '''
"""Tests for institutional metadata (Stage 2 req 1.5)."""
import pytest
from datetime import datetime, timezone
from athena_x_runtime_institutional_metadata import (
    InstitutionalMetadata,
    DataStatus,
    AssetClass,
    TradingSession,
    ProviderDefaults,
    create_metadata,
)


def test_metadata_has_10_mandatory_fields():
    """All 10 institutional metadata fields are present and required."""
    m = create_metadata(
        provider="yahoo",
        symbol="NVDA",
        asset_class=AssetClass.EQUITY,
    )
    # 10 mandatory fields
    assert m.provider == "yahoo"
    assert m.provider_latency >= 0
    assert m.download_timestamp.tzinfo is not None
    assert m.market_timestamp.tzinfo is not None
    assert m.timezone == "UTC"
    assert m.symbol == "NVDA"
    assert m.asset_class == "equity"
    assert 0.0 <= m.confidence_score <= 1.0
    assert m.status == "fresh"
    assert m.session == "regular"


def test_provider_defaults():
    """Each provider has a default confidence score."""
    assert ProviderDefaults.get_confidence("databento") == 0.98
    assert ProviderDefaults.get_confidence("yahoo") == 0.85
    assert ProviderDefaults.get_confidence("simulated") == 0.50
    # Unknown providers get a conservative default
    assert ProviderDefaults.get_confidence("unknown") == 0.80


def test_metadata_uses_provider_default_confidence():
    """If confidence not specified, uses provider default."""
    m = create_metadata(provider="databento", symbol="ES", asset_class="future")
    assert m.confidence_score == 0.98


def test_metadata_accepts_explicit_confidence():
    m = create_metadata(
        provider="yahoo",
        symbol="NVDA",
        asset_class="equity",
        confidence_score=0.99,
    )
    assert m.confidence_score == 0.99


def test_metadata_rejects_naive_timestamps():
    """Timestamps must be UTC-aware."""
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        InstitutionalMetadata(
            provider="yahoo",
            providerLatency=10,
            downloadTimestamp=datetime.now(),  # naive!
            marketTimestamp=datetime.now(timezone.utc),
            timezone="UTC",
            symbol="NVDA",
            assetClass=AssetClass.EQUITY,
            confidenceScore=0.85,
            status=DataStatus.FRESH,
            session=TradingSession.REGULAR,
        )


def test_metadata_rejects_invalid_confidence():
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        InstitutionalMetadata(
            provider="yahoo",
            providerLatency=10,
            downloadTimestamp=datetime.now(timezone.utc),
            marketTimestamp=datetime.now(timezone.utc),
            timezone="UTC",
            symbol="NVDA",
            assetClass=AssetClass.EQUITY,
            confidenceScore=1.5,  # invalid
            status=DataStatus.FRESH,
            session=TradingSession.REGULAR,
        )


def test_metadata_serializes_with_camel_case():
    """Metadata serializes to JSON with camelCase aliases."""
    m = create_metadata(provider="yahoo", symbol="NVDA", asset_class="equity")
    json_str = m.model_dump_json(by_alias=True)
    assert '"providerLatency"' in json_str
    assert '"downloadTimestamp"' in json_str
    assert '"marketTimestamp"' in json_str
    assert '"assetClass"' in json_str
    assert '"confidenceScore"' in json_str


def test_metadata_supports_all_asset_classes():
    """All 10 asset classes are supported."""
    for ac in AssetClass:
        m = create_metadata(provider="yahoo", symbol="X", asset_class=ac)
        assert m.asset_class == ac.value


def test_metadata_supports_all_sessions():
    """All 6 trading sessions are supported."""
    for s in TradingSession:
        m = create_metadata(
            provider="yahoo", symbol="X", asset_class="equity", session=s
        )
        assert m.session == s.value


def test_metadata_supports_all_statuses():
    """All 4 data statuses are supported."""
    for s in DataStatus:
        m = create_metadata(
            provider="yahoo", symbol="X", asset_class="equity", status=s
        )
        assert m.status == s.value
''')

# ============================================================================
# 2. SESSION AWARENESS — runtime/session-awareness/
# ============================================================================

w("runtime/session-awareness/pyproject.toml", '''
[project]
name = "athena-x-runtime-session-awareness"
version = "0.1.0"
description = "Trading session detection (overnight/pre/regular/post/weekend/holiday)"
requires-python = ">=3.11"
dependencies = [
    "pytz>=2024.1",
    "athena-x-runtime-logger",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/athena_x_runtime_session_awareness"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
''')

w("runtime/session-awareness/src/athena_x_runtime_session_awareness/__init__.py", '''
"""ATHENA-X session awareness."""
from .detector import SessionDetector, SessionInfo
from .holidays import is_holiday, get_holidays

__all__ = ["SessionDetector", "SessionInfo", "is_holiday", "get_holidays"]
__version__ = "0.1.0"
''')

w("runtime/session-awareness/src/athena_x_runtime_session_awareness/holidays.py", '''
"""US market holidays (NYSE/NASDAQ).

Static list of holidays for 2024-2027. In production, this would be fetched
from NYSE's published holiday calendar.
"""
from __future__ import annotations
from datetime import date


# NYSE-observed holidays (closed all day)
# Format: (month, day) for fixed holidays; float holidays computed separately
HOLIDAYS_2024_2027 = {
    # 2024
    date(2024, 1, 1):   "New Year's Day",
    date(2024, 1, 15):  "MLK Day",
    date(2024, 2, 19):  "Presidents Day",
    date(2024, 3, 29):  "Good Friday",
    date(2024, 5, 27):  "Memorial Day",
    date(2024, 6, 19):  "Juneteenth",
    date(2024, 7, 4):   "Independence Day",
    date(2024, 9, 2):   "Labor Day",
    date(2024, 11, 28): "Thanksgiving",
    date(2024, 12, 25): "Christmas",
    # 2025
    date(2025, 1, 1):   "New Year's Day",
    date(2025, 1, 20):  "MLK Day",
    date(2025, 2, 17):  "Presidents Day",
    date(2025, 4, 18):  "Good Friday",
    date(2025, 5, 26):  "Memorial Day",
    date(2025, 6, 19):  "Juneteenth",
    date(2025, 7, 4):   "Independence Day",
    date(2025, 9, 1):   "Labor Day",
    date(2025, 11, 27): "Thanksgiving",
    date(2025, 12, 25): "Christmas",
    # 2026
    date(2026, 1, 1):   "New Year's Day",
    date(2026, 1, 19):  "MLK Day",
    date(2026, 2, 16):  "Presidents Day",
    date(2026, 4, 3):   "Good Friday",
    date(2026, 5, 25):  "Memorial Day",
    date(2026, 6, 19):  "Juneteenth",
    date(2026, 7, 3):   "Independence Day (observed)",
    date(2026, 9, 7):   "Labor Day",
    date(2026, 11, 26): "Thanksgiving",
    date(2026, 12, 25): "Christmas",
    # 2027
    date(2027, 1, 1):   "New Year's Day",
    date(2027, 1, 18):  "MLK Day",
    date(2027, 2, 15):  "Presidents Day",
    date(2027, 3, 26):  "Good Friday",
    date(2027, 5, 31):  "Memorial Day",
    date(2027, 6, 18):  "Juneteenth (observed)",
    date(2027, 7, 5):   "Independence Day (observed)",
    date(2027, 9, 6):   "Labor Day",
    date(2027, 11, 25): "Thanksgiving",
    date(2027, 12, 24): "Christmas (observed)",
}


def is_holiday(d: date) -> bool:
    """Return True if the given date is an NYSE holiday."""
    return d in HOLIDAYS_2024_2027


def get_holidays() -> dict[date, str]:
    """Return the full holiday map."""
    return dict(HOLIDAYS_2024_2027)
''')

w("runtime/session-awareness/src/athena_x_runtime_session_awareness/detector.py", '''
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
''')

w("runtime/session-awareness/tests/__init__.py", "")
w("runtime/session-awareness/tests/test_detector.py", '''
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
    """July 4 is a holiday."""
    d = SessionDetector()
    info = d.detect(et_time(7, 4, 10, 0))
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
''')

# ============================================================================
# 3. RAW ARCHIVAL — runtime/raw-archival/
# ============================================================================

w("runtime/raw-archival/pyproject.toml", '''
[project]
name = "athena-x-runtime-raw-archival"
version = "0.1.0"
description = "Filesystem archival of raw payloads (provider/yyyy/mm/dd/hh/) — Stage 2 req 1.6"
requires-python = ">=3.11"
dependencies = [
    "athena-x-runtime-logger",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/athena_x_runtime_raw_archival"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
''')

w("runtime/raw-archival/src/athena_x_runtime_raw_archival/__init__.py", '''
"""ATHENA-X raw archival."""
from .archiver import RawArchiver, ArchivedFile

__all__ = ["RawArchiver", "ArchivedFile"]
__version__ = "0.1.0"
''')

w("runtime/raw-archival/src/athena_x_runtime_raw_archival/archiver.py", '''
"""Raw payload archival — Stage 2 req 1.6.

Every raw payload is archived before parsing. Directory structure:
    raw_landing/
    └── <provider>/
        └── <yyyy>/
            └── <mm>/
                └── <dd>/
                    └── <hh>/
                        └── <uuid>.json

Never discards original data. If parsing fails later, the source is still
available for replay/audit.
"""
from __future__ import annotations
import json
import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from athena_x_runtime_logger import get_logger

log = get_logger("runtime.raw-archival")


@dataclass(frozen=True)
class ArchivedFile:
    """Metadata about an archived raw payload."""
    path: str
    provider: str
    size_bytes: int
    archived_at: datetime


class RawArchiver:
    """Archives raw payloads to the filesystem.

    Usage:
        archiver = RawArchiver(base_path="/var/lib/athena-x/raw_landing")
        archived = archiver.archive(
            provider="yahoo",
            payload={"symbol": "NVDA", "last": 128.45, ...},
            timestamp=datetime.now(timezone.utc),
        )
        # archived.path = "/var/lib/athena-x/raw_landing/yahoo/2026/07/17/13/<uuid>.json"
    """

    def __init__(self, base_path: str | Path = "raw_landing"):
        self._base_path = Path(base_path)
        self._base_path.mkdir(parents=True, exist_ok=True)

    def archive(
        self,
        *,
        provider: str,
        payload: Any,
        timestamp: datetime | None = None,
    ) -> ArchivedFile:
        """Archive a raw payload.

        Args:
            provider: provider slug (e.g., "yahoo", "finnhub")
            payload: any JSON-serializable payload
            timestamp: optional — defaults to now (UTC)

        Returns:
            ArchivedFile with the path where the payload was written.
        """
        ts = timestamp or datetime.now(timezone.utc)
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)

        # Build directory: base/provider/yyyy/mm/dd/hh/
        dir_path = self._base_path / provider / ts.strftime("%Y/%m/%d/%H")
        dir_path.mkdir(parents=True, exist_ok=True)

        # Filename: uuid.json (avoids collisions)
        file_id = str(uuid.uuid4())
        file_path = dir_path / f"{file_id}.json"

        # Write payload + archival metadata
        archive_record = {
            "archive_id": file_id,
            "provider": provider,
            "archived_at": ts.isoformat(),
            "payload": payload,
        }

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(archive_record, f, default=str, ensure_ascii=False)

        size = file_path.stat().st_size
        log.debug("payload_archived",
                  provider=provider,
                  path=str(file_path),
                  size_bytes=size)

        return ArchivedFile(
            path=str(file_path),
            provider=provider,
            size_bytes=size,
            archived_at=ts,
        )

    def read(self, path: str | Path) -> dict:
        """Read an archived payload back from disk."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Archived file not found: {path}")
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def list_provider_hour(
        self,
        provider: str,
        year: int,
        month: int,
        day: int,
        hour: int,
    ) -> list[Path]:
        """List all archived files for a provider in a specific hour."""
        dir_path = self._base_path / provider / f"{year:04d}/{month:02d}/{day:02d}/{hour:02d}"
        if not dir_path.exists():
            return []
        return sorted(dir_path.glob("*.json"))

    def list_provider_day(
        self,
        provider: str,
        year: int,
        month: int,
        day: int,
    ) -> list[Path]:
        """List all archived files for a provider on a specific day."""
        dir_path = self._base_path / provider / f"{year:04d}/{month:02d}/{day:02d}"
        if not dir_path.exists():
            return []
        return sorted(dir_path.glob("**/*.json"))

    def storage_stats(self) -> dict:
        """Return storage statistics."""
        total_files = 0
        total_bytes = 0
        per_provider = {}

        for provider_dir in self._base_path.iterdir():
            if not provider_dir.is_dir():
                continue
            provider_files = list(provider_dir.rglob("*.json"))
            provider_bytes = sum(f.stat().st_size for f in provider_files)
            per_provider[provider_dir.name] = {
                "files": len(provider_files),
                "bytes": provider_bytes,
            }
            total_files += len(provider_files)
            total_bytes += provider_bytes

        return {
            "total_files": total_files,
            "total_bytes": total_bytes,
            "per_provider": per_provider,
        }
''')

w("runtime/raw-archival/tests/__init__.py", "")
w("runtime/raw-archival/tests/test_archiver.py", '''
"""Tests for raw archival (Stage 2 req 1.6)."""
import json
import pytest
from datetime import datetime, timezone
from pathlib import Path
from athena_x_runtime_raw_archival import RawArchiver


def test_archive_creates_file_with_correct_structure(tmp_path):
    """Archived files are stored under provider/yyyy/mm/dd/hh/."""
    archiver = RawArchiver(base_path=tmp_path)
    ts = datetime(2026, 7, 17, 13, 45, tzinfo=timezone.utc)

    result = archiver.archive(
        provider="yahoo",
        payload={"symbol": "NVDA", "last": 128.45},
        timestamp=ts,
    )

    # Path should be: tmp_path/yahoo/2026/07/17/13/<uuid>.json
    expected_dir = tmp_path / "yahoo" / "2026" / "07" / "17" / "13"
    assert expected_dir.exists()
    archived_files = list(expected_dir.glob("*.json"))
    assert len(archived_files) == 1
    assert result.path == str(archived_files[0])


def test_archive_preserves_payload(tmp_path):
    """Archived payload can be read back exactly as written."""
    archiver = RawArchiver(base_path=tmp_path)
    payload = {"symbol": "SPY", "last": 456.78, "bid": 456.76, "ask": 456.80}

    result = archiver.archive(provider="finnhub", payload=payload)
    read_back = archiver.read(result.path)

    assert read_back["payload"] == payload
    assert read_back["provider"] == "finnhub"
    assert "archived_at" in read_back
    assert "archive_id" in read_back


def test_archive_default_timestamp_is_now(tmp_path):
    """If no timestamp provided, uses current UTC time."""
    archiver = RawArchiver(base_path=tmp_path)
    before = datetime.now(timezone.utc)
    result = archiver.archive(provider="yahoo", payload={"x": 1})
    after = datetime.now(timezone.utc)

    assert before <= result.archived_at <= after


def test_multiple_payloads_get_unique_filenames(tmp_path):
    """Multiple payloads archived in the same hour get unique filenames."""
    archiver = RawArchiver(base_path=tmp_path)
    ts = datetime(2026, 7, 17, 13, 45, tzinfo=timezone.utc)

    paths = set()
    for i in range(10):
        r = archiver.archive(provider="yahoo", payload={"i": i}, timestamp=ts)
        paths.add(r.path)

    assert len(paths) == 10  # all unique


def test_list_provider_hour(tmp_path):
    """list_provider_hour returns all files for a specific hour."""
    archiver = RawArchiver(base_path=tmp_path)
    ts = datetime(2026, 7, 17, 13, 45, tzinfo=timezone.utc)

    for i in range(3):
        archiver.archive(provider="yahoo", payload={"i": i}, timestamp=ts)
    # Different hour
    archiver.archive(
        provider="yahoo", payload={"i": 99},
        timestamp=datetime(2026, 7, 17, 14, 0, tzinfo=timezone.utc),
    )

    files = archiver.list_provider_hour("yahoo", 2026, 7, 17, 13)
    assert len(files) == 3


def test_list_provider_day(tmp_path):
    """list_provider_day returns all files across all hours of a day."""
    archiver = RawArchiver(base_path=tmp_path)
    for hour in range(5):
        archiver.archive(
            provider="yahoo", payload={"h": hour},
            timestamp=datetime(2026, 7, 17, hour, 0, tzinfo=timezone.utc),
        )

    files = archiver.list_provider_day("yahoo", 2026, 7, 17)
    assert len(files) == 5


def test_storage_stats(tmp_path):
    """storage_stats returns aggregate counts and bytes per provider."""
    archiver = RawArchiver(base_path=tmp_path)
    for i in range(5):
        archiver.archive(provider="yahoo", payload={"i": i})
    for i in range(3):
        archiver.archive(provider="finnhub", payload={"i": i})

    stats = archiver.storage_stats()
    assert stats["total_files"] == 8
    assert stats["total_bytes"] > 0
    assert stats["per_provider"]["yahoo"]["files"] == 5
    assert stats["per_provider"]["finnhub"]["files"] == 3


def test_archive_handles_non_serializable_payload(tmp_path):
    """Archiver uses default=str to handle non-JSON-serializable values."""
    archiver = RawArchiver(base_path=tmp_path)
    # datetime is not natively JSON-serializable
    payload = {"timestamp": datetime(2026, 7, 17, tzinfo=timezone.utc)}

    result = archiver.archive(provider="yahoo", payload=payload)
    read_back = archiver.read(result.path)
    # datetime should be converted to ISO string
    assert "2026-07-17" in read_back["payload"]["timestamp"]


def test_read_nonexistent_raises(tmp_path):
    archiver = RawArchiver(base_path=tmp_path)
    with pytest.raises(FileNotFoundError):
        archiver.read(tmp_path / "nonexistent.json")
''')

# ============================================================================
# 4. DATA FRESHNESS — runtime/data-freshness/
# ============================================================================

w("runtime/data-freshness/pyproject.toml", '''
[project]
name = "athena-x-runtime-data-freshness"
version = "0.1.0"
description = "Data freshness tracking (fresh/delayed/stale) — Stage 2 req 1.9"
requires-python = ">=3.11"
dependencies = [
    "athena-x-runtime-logger",
    "athena-x-runtime-institutional-metadata",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/athena_x_runtime_data_freshness"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
''')

w("runtime/data-freshness/src/athena_x_runtime_data_freshness/__init__.py", '''
"""ATHENA-X data freshness tracking."""
from .tracker import FreshnessTracker, FreshnessStatus, StreamStats

__all__ = ["FreshnessTracker", "FreshnessStatus", "StreamStats"]
__version__ = "0.1.0"
''')

w("runtime/data-freshness/src/athena_x_runtime_data_freshness/tracker.py", '''
"""Data freshness tracker — Stage 2 req 1.9.

Every stream publishes:
  - expected_update_frequency (e.g., 1s for ES, 15s for VIX)
  - actual_update_frequency (rolling avg)
  - last_received_timestamp
  - status: fresh / delayed / stale

Status definitions:
  - fresh:  last_received within 1.5× expected frequency
  - delayed: last_received within 3× expected frequency
  - stale:  last_received > 3× expected frequency

This prevents the AI from making decisions on outdated information.
"""
from __future__ import annotations
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from threading import Lock
from typing import Deque

from athena_x_runtime_logger import get_logger

log = get_logger("runtime.data-freshness")


class FreshnessStatus(str, Enum):
    FRESH = "fresh"
    DELAYED = "delayed"
    STALE = "stale"
    NO_DATA = "no-data"


@dataclass
class StreamStats:
    """Statistics for a single data stream (symbol + provider)."""
    stream_id: str  # "{provider}:{symbol}"
    expected_frequency_s: float  # expected update interval in seconds
    last_received: datetime | None = None
    actual_frequency_s: float | None = None  # rolling avg
    total_received: int = 0
    status: FreshnessStatus = FreshnessStatus.NO_DATA
    recent_intervals: Deque[float] = field(default_factory=lambda: deque(maxlen=100))


class FreshnessTracker:
    """Tracks freshness of all data streams.

    Usage:
        tracker = FreshnessTracker()
        tracker.register_stream("yahoo:NVDA", expected_frequency_s=1.0)
        tracker.record_receipt("yahoo:NVDA")
        status = tracker.get_status("yahoo:NVDA")
        # status.status == FreshnessStatus.FRESH
    """

    def __init__(self):
        self._streams: dict[str, StreamStats] = {}
        self._lock = Lock()

    def register_stream(self, stream_id: str, expected_frequency_s: float) -> None:
        """Register a new stream with its expected update frequency."""
        with self._lock:
            if stream_id not in self._streams:
                self._streams[stream_id] = StreamStats(
                    stream_id=stream_id,
                    expected_frequency_s=expected_frequency_s,
                )
                log.info("stream_registered",
                         stream_id=stream_id,
                         expected_frequency_s=expected_frequency_s)

    def record_receipt(self, stream_id: str, timestamp: datetime | None = None) -> FreshnessStatus:
        """Record that a stream received an update.

        Args:
            stream_id: "{provider}:{symbol}" identifier
            timestamp: optional — defaults to now (UTC)

        Returns:
            The new FreshnessStatus for this stream.
        """
        ts = timestamp or datetime.now(timezone.utc)
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)

        with self._lock:
            stream = self._streams.get(stream_id)
            if stream is None:
                log.warning("unregistered_stream", stream_id=stream_id)
                return FreshnessStatus.NO_DATA

            # Compute interval since last receipt
            if stream.last_received is not None:
                interval = (ts - stream.last_received).total_seconds()
                stream.recent_intervals.append(interval)
                # Rolling average
                if stream.recent_intervals:
                    stream.actual_frequency_s = sum(stream.recent_intervals) / len(stream.recent_intervals)

            stream.last_received = ts
            stream.total_received += 1
            stream.status = self._compute_status(stream, ts)
            return stream.status

    def get_status(self, stream_id: str) -> FreshnessStatus:
        """Get the current status of a stream (recomputes staleness)."""
        with self._lock:
            stream = self._streams.get(stream_id)
            if stream is None:
                return FreshnessStatus.NO_DATA
            stream.status = self._compute_status(stream, datetime.now(timezone.utc))
            return stream.status

    def get_stats(self, stream_id: str) -> StreamStats | None:
        """Get full stats for a stream."""
        with self._lock:
            stream = self._streams.get(stream_id)
            if stream is None:
                return None
            # Recompute status before returning
            stream.status = self._compute_status(stream, datetime.now(timezone.utc))
            return stream

    def list_all_streams(self) -> list[StreamStats]:
        """List all registered streams with current status."""
        with self._lock:
            now = datetime.now(timezone.utc)
            for stream in self._streams.values():
                stream.status = self._compute_status(stream, now)
            return list(self._streams.values())

    def list_stale_streams(self) -> list[StreamStats]:
        """Return only stale streams (for alerting)."""
        return [s for s in self.list_all_streams() if s.status == FreshnessStatus.STALE]

    def _compute_status(self, stream: StreamStats, now: datetime) -> FreshnessStatus:
        """Compute the freshness status based on time since last receipt."""
        if stream.last_received is None:
            return FreshnessStatus.NO_DATA

        age_s = (now - stream.last_received).total_seconds()
        expected = stream.expected_frequency_s

        if age_s <= 1.5 * expected:
            return FreshnessStatus.FRESH
        if age_s <= 3.0 * expected:
            return FreshnessStatus.DELAYED
        return FreshnessStatus.STALE
''')

w("runtime/data-freshness/tests/__init__.py", "")
w("runtime/data-freshness/tests/test_tracker.py", '''
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
''')

# ============================================================================
# 5. PROVIDER BASE — providers/base/
# ============================================================================

w("providers/base/pyproject.toml", '''
[project]
name = "athena-x-provider-base"
version = "0.1.0"
description = "MarketDataProvider protocol + shared types"
requires-python = ">=3.11"
dependencies = [
    "pydantic>=2.9.0",
    "athena-x-runtime-logger",
    "athena-x-runtime-institutional-metadata",
    "athena-x-runtime-raw-archival",
    "athena-x-runtime-data-freshness",
    "athena-x-runtime-event-bus",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/athena_x_provider_base"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
''')

w("providers/base/src/athena_x_provider_base/__init__.py", '''
"""Market data provider base protocol."""
from .types import Quote, Bar, Trade, OptionChain, OptionRow, NewsArticle
from .provider import MarketDataProvider, ProviderResult, ProviderError
from .base_adapter import BaseProviderAdapter

__all__ = [
    "Quote", "Bar", "Trade", "OptionChain", "OptionRow", "NewsArticle",
    "MarketDataProvider", "ProviderResult", "ProviderError",
    "BaseProviderAdapter",
]
__version__ = "0.1.0"
''')

w("providers/base/src/athena_x_provider_base/types.py", '''
"""Canonical data types produced by providers.

These are the OUTPUT types — what providers return after parsing their
provider-specific responses. Layer 3 (Standardization) further normalizes
these into the database canonical schema.
"""
from __future__ import annotations
from datetime import date, datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class Quote(BaseModel):
    """A real-time quote for a symbol."""
    model_config = ConfigDict(populate_by_name=True)
    symbol: str
    last: float
    bid: float | None = None
    ask: float | None = None
    high: float | None = None
    low: float | None = None
    open: float | None = None
    prev_close: float | None = None
    volume: int | None = None
    change: float | None = None
    change_percent: float | None = None
    timestamp: datetime


class Bar(BaseModel):
    """An OHLCV bar."""
    timestamp: int = Field(description="unix-millis")
    open: float
    high: float
    low: float
    close: float
    volume: int


class Trade(BaseModel):
    """An individual trade print."""
    symbol: str
    price: float
    size: int
    side: str | None = None  # 'buy' | 'sell' | 'unknown'
    timestamp: datetime


class OptionRow(BaseModel):
    """A single row in an options chain."""
    strike: float
    expiry: date
    option_type: str  # 'call' | 'put'
    bid: float | None = None
    ask: float | None = None
    last: float | None = None
    volume: int | None = None
    open_interest: int | None = None
    iv: float | None = None
    delta: float | None = None
    gamma: float | None = None
    theta: float | None = None
    vega: float | None = None
    rho: float | None = None


class OptionChain(BaseModel):
    """An options chain for a symbol on a specific expiry."""
    symbol: str
    expiry: date
    rows: list[OptionRow]


class NewsArticle(BaseModel):
    """A news article."""
    model_config = ConfigDict(populate_by_name=True)
    id: str
    source: str
    headline: str
    summary: str | None = None
    url: str | None = None
    raw_content: str | None = None
    published_at: datetime
    symbols: list[str] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)
    sentiment: float | None = None  # left blank in Stage 2; filled in Stage 10
''')

w("providers/base/src/athena_x_provider_base/provider.py", '''
"""MarketDataProvider protocol + result types."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Protocol, runtime_checkable

from .types import Quote, Bar, Trade, OptionChain, NewsArticle


@dataclass
class ProviderResult:
    """Wraps a successful provider response with metadata."""
    data: Any  # Quote, Bar, Trade, OptionChain, or NewsArticle
    provider: str
    latency_ms: int
    raw_payload: Any  # original provider response (for archival)
    market_timestamp: datetime


class ProviderError(Exception):
    """Raised when a provider call fails."""
    def __init__(self, provider: str, message: str, status_code: int | None = None):
        self.provider = provider
        self.status_code = status_code
        super().__init__(f"[{provider}] {message}")


@runtime_checkable
class MarketDataProvider(Protocol):
    """Protocol that all provider adapters implement.

    Stage 2 rule: providers ONLY download data. Never calculate.
    """

    name: str
    transport: str
    asset_classes: list[str]

    async def fetch_quote(self, symbol: str) -> ProviderResult:
        """Fetch a real-time quote for a symbol."""
        ...

    async def fetch_bars(
        self,
        symbol: str,
        timeframe: str,
        count: int,
    ) -> list[ProviderResult]:
        """Fetch historical OHLCV bars."""
        ...

    async def fetch_option_chain(
        self,
        symbol: str,
        expiry: date,
    ) -> ProviderResult:
        """Fetch an options chain for a symbol on a specific expiry."""
        ...

    async def fetch_news(
        self,
        symbols: list[str] | None = None,
        categories: list[str] | None = None,
        limit: int = 50,
    ) -> list[ProviderResult]:
        """Fetch news articles."""
        ...

    async def health_check(self) -> dict:
        """Return provider health metrics."""
        ...
''')

w("providers/base/src/athena_x_provider_base/base_adapter.py", '''
"""Base provider adapter with common functionality.

Provides:
- API key management
- Rate limiting (simple)
- Latency measurement
- Raw payload archival (via RawArchiver)
- Freshness tracking (via FreshnessTracker)
- Health metric collection

Concrete providers subclass this and implement fetch_* methods.
"""
from __future__ import annotations
import time
from datetime import datetime, timezone
from typing import Any

from athena_x_runtime_logger import get_logger
from athena_x_runtime_institutional_metadata import create_metadata, InstitutionalMetadata
from athena_x_runtime_raw_archival import RawArchiver
from athena_x_runtime_data_freshness import FreshnessTracker

from .provider import ProviderResult, ProviderError

log = get_logger("providers.base")


class BaseProviderAdapter:
    """Base class for provider adapters.

    Subclasses must implement:
      - async def _fetch_quote(self, symbol: str) -> tuple[Any, datetime]
      - async def _fetch_bars(...) -> list[tuple[Any, datetime]]
      - etc.

    The _fetch_* methods return (raw_payload, market_timestamp) tuples.
    The base class handles archival, freshness tracking, and metadata.
    """

    name: str = "base"
    transport: str = "unknown"
    asset_classes: list[str] = []

    def __init__(
        self,
        api_key: str | None = None,
        archiver: RawArchiver | None = None,
        freshness_tracker: FreshnessTracker | None = None,
    ):
        self.api_key = api_key
        self._archiver = archiver
        self._freshness = freshness_tracker
        self._call_count = 0
        self._success_count = 0
        self._failure_count = 0
        self._latencies: list[float] = []
        self._last_success: datetime | None = None

    async def fetch_quote(self, symbol: str) -> ProviderResult:
        """Fetch a quote. Measures latency, archives raw, tracks freshness."""
        start = time.monotonic()
        try:
            raw_payload, market_ts = await self._fetch_quote(symbol)
            latency_ms = int((time.monotonic() - start) * 1000)
            self._record_success(latency_ms)
            self._archive(symbol, raw_payload)
            self._record_freshness(symbol)
            return ProviderResult(
                data=raw_payload,
                provider=self.name,
                latency_ms=latency_ms,
                raw_payload=raw_payload,
                market_timestamp=market_ts,
            )
        except Exception as e:
            self._record_failure()
            raise ProviderError(self.name, str(e)) from e

    async def _fetch_quote(self, symbol: str) -> tuple[Any, datetime]:
        raise NotImplementedError(f"{self.name} does not implement fetch_quote")

    async def _fetch_bars(self, symbol: str, timeframe: str, count: int) -> list[tuple[Any, datetime]]:
        raise NotImplementedError(f"{self.name} does not implement fetch_bars")

    async def _fetch_option_chain(self, symbol: str, expiry) -> tuple[Any, datetime]:
        raise NotImplementedError(f"{self.name} does not implement fetch_option_chain")

    async def _fetch_news(self, symbols=None, categories=None, limit=50) -> list[tuple[Any, datetime]]:
        raise NotImplementedError(f"{self.name} does not implement fetch_news")

    def _archive(self, symbol: str, payload: Any) -> None:
        if self._archiver is not None:
            self._archiver.archive(provider=self.name, payload=payload)

    def _record_freshness(self, symbol: str) -> None:
        if self._freshness is not None:
            stream_id = f"{self.name}:{symbol}"
            try:
                self._freshness.record_receipt(stream_id)
            except Exception:
                pass  # freshness tracking is best-effort

    def _record_success(self, latency_ms: int) -> None:
        self._call_count += 1
        self._success_count += 1
        self._latencies.append(latency_ms)
        if len(self._latencies) > 100:
            self._latencies = self._latencies[-100:]
        self._last_success = datetime.now(timezone.utc)

    def _record_failure(self) -> None:
        self._call_count += 1
        self._failure_count += 1

    async def health_check(self) -> dict:
        """Return provider health metrics (Stage 2 req 1.7)."""
        avg_latency = (
            sum(self._latencies) / len(self._latencies)
            if self._latencies else 0.0
        )
        success_rate = (
            self._success_count / self._call_count
            if self._call_count > 0 else 0.0
        )
        staleness_ms = 0.0
        if self._last_success is not None:
            staleness_ms = (
                datetime.now(timezone.utc) - self._last_success
            ).total_seconds() * 1000

        return {
            "provider": self.name,
            "connection": "connected" if self._last_success is not None else "disconnected",
            "delay": avg_latency,
            "missingBars": 0,
            "missingTicks": 0,
            "apiErrors": self._failure_count,
            "failoverCount": 0,
            "freshness": staleness_ms,
            "reliabilityScore": success_rate,
            "total_calls": self._call_count,
            "successful_calls": self._success_count,
            "failed_calls": self._failure_count,
            "last_successful_update": self._last_success.isoformat() if self._last_success else None,
        }
''')

w("providers/base/tests/__init__.py", "")
w("providers/base/tests/test_types.py", '''
"""Tests for provider base types."""
import pytest
from datetime import datetime, timezone, date
from athena_x_provider_base import Quote, Bar, Trade, OptionChain, OptionRow, NewsArticle


def test_quote_serialization():
    q = Quote(
        symbol="NVDA",
        last=128.45,
        bid=128.44,
        ask=128.46,
        timestamp=datetime.now(timezone.utc),
    )
    assert q.symbol == "NVDA"
    assert q.last == 128.45


def test_bar_serialization():
    b = Bar(timestamp=1700000000000, open=100, high=105, low=99, close=104, volume=1000)
    assert b.open == 100
    assert b.volume == 1000


def test_option_chain():
    chain = OptionChain(
        symbol="NVDA",
        expiry=date(2026, 7, 18),
        rows=[
            OptionRow(strike=125, expiry=date(2026, 7, 18), option_type="call", iv=0.45),
            OptionRow(strike=130, expiry=date(2026, 7, 18), option_type="put", iv=0.42),
        ],
    )
    assert chain.symbol == "NVDA"
    assert len(chain.rows) == 2


def test_news_article():
    a = NewsArticle(
        id="abc-123",
        source="reuters",
        headline="NVDA beats Q3 estimates",
        published_at=datetime.now(timezone.utc),
        symbols=["NVDA"],
        categories=["earnings"],
    )
    assert a.sentiment is None  # left blank in Stage 2
    assert a.source == "reuters"
''')

# ============================================================================
# 6. SIMULATED PROVIDER — providers/simulated/ (dev only)
# ============================================================================

w("providers/simulated/pyproject.toml", '''
[project]
name = "athena-x-provider-simulated"
version = "0.1.0"
description = "Simulated provider for dev/test only — never in production"
requires-python = ">=3.11"
dependencies = [
    "athena-x-provider-base",
    "athena-x-runtime-logger",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/athena_x_provider_simulated"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
''')

w("providers/simulated/src/athena_x_provider_simulated/__init__.py", '''
"""Simulated provider — DEV ONLY. Never used in production."""
from .adapter import SimulatedAdapter

__all__ = ["SimulatedAdapter"]
__version__ = "0.1.0"
''')

w("providers/simulated/src/athena_x_provider_simulated/adapter.py", '''
"""Simulated provider for development and testing.

Generates deterministic mock data using a seeded random generator.
NEVER used in production — the provider failover chain excludes it.
"""
from __future__ import annotations
import random
from datetime import datetime, timezone, timedelta
from typing import Any

from athena_x_provider_base import Quote, Bar
from athena_x_provider_base.base_adapter import BaseProviderAdapter
from athena_x_provider_base.provider import ProviderResult


# Base prices for common symbols (deterministic starting points)
BASE_PRICES = {
    "SPY": 450.0, "ES": 4500.0, "SPX": 4500.0,
    "QQQ": 380.0, "NQ": 16000.0,
    "DIA": 380.0, "IWM": 200.0, "SOXX": 200.0,
    "VIX": 15.0, "VVIX": 90.0, "MOVE": 80.0,
    "TNX": 4.5, "DXY": 100.0, "USDJPY": 150.0,
    "Gold": 2000.0, "Oil": 80.0, "Copper": 4.0,
    "BTC-USD": 65000.0, "ETH-USD": 3500.0,
    "NVDA": 128.0, "AAPL": 225.0, "MSFT": 420.0,
    "TSLA": 250.0, "META": 500.0, "AMZN": 185.0, "GOOGL": 175.0,
}


class SimulatedAdapter(BaseProviderAdapter):
    """Simulated provider. Generates deterministic mock quotes/bars."""

    name = "simulated"
    transport = "in-process"
    asset_classes = ["equity", "etf", "index", "future", "currency",
                     "commodity", "yield", "volatility", "crypto"]

    def __init__(self, seed: int = 42, **kwargs):
        super().__init__(api_key=None, **kwargs)
        self._rng = random.Random(seed)
        self._prices = dict(BASE_PRICES)

    async def _fetch_quote(self, symbol: str) -> tuple[dict, datetime]:
        """Generate a simulated quote with a small random walk."""
        base = self._prices.get(symbol, 100.0)
        # Random walk: ±0.5%
        change_pct = self._rng.gauss(0, 0.005)
        new_price = base * (1 + change_pct)
        self._prices[symbol] = new_price

        bid = new_price - self._rng.uniform(0.01, 0.05)
        ask = new_price + self._rng.uniform(0.01, 0.05)
        now = datetime.now(timezone.utc)

        quote = {
            "symbol": symbol,
            "last": round(new_price, 4),
            "bid": round(bid, 4),
            "ask": round(ask, 4),
            "high": round(new_price * 1.01, 4),
            "low": round(new_price * 0.99, 4),
            "open": round(base, 4),
            "prev_close": round(base, 4),
            "volume": self._rng.randint(100000, 5000000),
            "change": round(new_price - base, 4),
            "change_percent": round(change_pct * 100, 4),
            "timestamp": now.isoformat(),
        }
        return quote, now

    async def _fetch_bars(self, symbol: str, timeframe: str, count: int) -> list[tuple[dict, datetime]]:
        """Generate simulated historical bars."""
        base = self._prices.get(symbol, 100.0)
        bars = []
        now = datetime.now(timezone.utc)

        # Time delta per timeframe
        deltas = {
            "1m": timedelta(minutes=1), "5m": timedelta(minutes=5),
            "15m": timedelta(minutes=15), "30m": timedelta(minutes=30),
            "1h": timedelta(hours=1), "4h": timedelta(hours=4),
            "1D": timedelta(days=1), "1W": timedelta(weeks=1),
            "1M": timedelta(days=30),
        }
        delta = deltas.get(timeframe, timedelta(minutes=1))

        for i in range(count):
            ts = now - delta * (count - i)
            open_p = base * (1 + self._rng.gauss(0, 0.01))
            close_p = open_p * (1 + self._rng.gauss(0, 0.005))
            high_p = max(open_p, close_p) * (1 + self._rng.uniform(0, 0.005))
            low_p = min(open_p, close_p) * (1 - self._rng.uniform(0, 0.005))

            bar = {
                "symbol": symbol,
                "timestamp": int(ts.timestamp() * 1000),
                "open": round(open_p, 4),
                "high": round(high_p, 4),
                "low": round(low_p, 4),
                "close": round(close_p, 4),
                "volume": self._rng.randint(10000, 1000000),
            }
            bars.append((bar, ts))
            base = close_p  # next bar starts where this one ended

        return bars

    async def health_check(self) -> dict:
        health = await super().health_check()
        health["connection"] = "connected"
        health["reliabilityScore"] = 1.0
        return health
''')

w("providers/simulated/tests/__init__.py", "")
w("providers/simulated/tests/test_adapter.py", '''
"""Tests for simulated provider."""
import pytest
from athena_x_provider_simulated import SimulatedAdapter


@pytest.fixture
async def provider():
    p = SimulatedAdapter(seed=42)
    yield p


async def test_fetch_quote_returns_valid_data(provider):
    result = await provider.fetch_quote("NVDA")
    assert result.provider == "simulated"
    assert result.data["symbol"] == "NVDA"
    assert result.data["last"] > 0
    assert "bid" in result.data
    assert "ask" in result.data
    assert result.latency_ms >= 0


async def test_quote_random_walk_changes_price(provider):
    """Successive quotes have different prices (random walk)."""
    r1 = await provider.fetch_quote("SPY")
    r2 = await provider.fetch_quote("SPY")
    assert r1.data["last"] != r2.data["last"]


async def test_deterministic_with_same_seed():
    """Same seed produces same sequence of quotes."""
    p1 = SimulatedAdapter(seed=123)
    p2 = SimulatedAdapter(seed=123)
    r1 = await p1.fetch_quote("SPY")
    r2 = await p2.fetch_quote("SPY")
    assert r1.data["last"] == r2.data["last"]


async def test_fetch_bars(provider):
    results = await provider.fetch_quote("SPY")  # warm up
    bars = await provider.fetch_bars("SPY", "1m", 10)
    # Note: base adapter doesn't wrap _fetch_bars the same way as _fetch_quote.
    # Direct call returns raw tuples.
    assert len(bars) == 10
    for bar, ts in bars:
        assert bar["symbol"] == "SPY"
        assert bar["open"] > 0
        assert bar["high"] >= bar["open"]
        assert bar["low"] <= bar["open"]


async def test_health_check(provider):
    await provider.fetch_quote("SPY")
    health = await provider.health_check()
    assert health["provider"] == "simulated"
    assert health["connection"] == "connected"
    assert health["reliabilityScore"] == 1.0


async def test_unknown_symbol_uses_default_price(provider):
    """Unknown symbols start at $100."""
    result = await provider.fetch_quote("UNKNOWN")
    assert 90 < result.data["last"] < 110  # near default $100 after small walk
''')

# ============================================================================
# 7. YAHOO PROVIDER — providers/yahoo/ (real impl)
# ============================================================================

w("providers/yahoo/pyproject.toml", '''
[project]
name = "athena-x-provider-yahoo"
version = "0.1.0"
description = "Yahoo Finance provider adapter (real implementation)"
requires-python = ">=3.11"
dependencies = [
    "athena-x-provider-base",
    "athena-x-runtime-logger",
    "httpx>=0.27.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/athena_x_provider_yahoo"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
''')

w("providers/yahoo/src/athena_x_provider_yahoo/__init__.py", '''
"""Yahoo Finance provider."""
from .adapter import YahooAdapter

__all__ = ["YahooAdapter"]
__version__ = "0.1.0"
''')

w("providers/yahoo/src/athena_x_provider_yahoo/adapter.py", '''
"""Yahoo Finance provider adapter.

Uses Yahoo's public (undocumented) API endpoints:
  - /v8/finance/chart/{symbol} — historical bars + quotes
  - /v7/finance/quote?symbols=... — batch quotes (currently rate-limited)

No API key required, but rate-limited. Falls back to /v8/finance/chart
for individual quotes which is more reliable.
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any

import httpx

from athena_x_provider_base.base_adapter import BaseProviderAdapter
from athena_x_provider_base.provider import ProviderError


YAHOO_BASE_URL = "https://query1.finance.yahoo.com"
YAHOO_CHART_URL = f"{YAHOO_BASE_URL}/v8/finance/chart/{{symbol}}"


class YahooAdapter(BaseProviderAdapter):
    """Yahoo Finance provider adapter.

    Layer 1 — Provider Adapters.
    ONLY downloads data. NEVER calculates, validates, or standardizes.
    """

    name = "yahoo"
    transport = "REST"
    asset_classes = ["equity", "etf", "index", "currency", "commodity",
                     "yield", "volatility", "future"]

    def __init__(self, api_key: str | None = None, **kwargs):
        # Yahoo doesn't require an API key for public endpoints
        super().__init__(api_key=None, **kwargs)
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                headers={
                    "User-Agent": "Mozilla/5.0 (ATHENA-X research)",
                    "Accept": "application/json",
                },
                timeout=httpx.Timeout(10.0, connect=5.0),
            )
        return self._client

    async def _fetch_quote(self, symbol: str) -> tuple[dict, datetime]:
        """Fetch a quote using Yahoo's chart endpoint."""
        client = await self._get_client()
        url = YAHOO_CHART_URL.format(symbol=symbol)
        params = {"interval": "1m", "range": "1d"}

        resp = await client.get(url, params=params)
        if resp.status_code != 200:
            raise ProviderError(
                "yahoo",
                f"HTTP {resp.status_code}: {resp.text[:200]}",
                status_code=resp.status_code,
            )

        data = resp.json()
        result = data.get("chart", {}).get("result", [])
        if not result:
            raise ProviderError("yahoo", f"No data for symbol: {symbol}")

        chart = result[0]
        meta = chart.get("meta", {})

        # Extract quote fields from metadata
        quote = {
            "symbol": meta.get("symbol", symbol),
            "last": meta.get("regularMarketPrice", 0.0),
            "bid": meta.get("bid", 0.0) or None,
            "ask": meta.get("ask", 0.0) or None,
            "high": meta.get("regularMarketDayHigh", 0.0) or None,
            "low": meta.get("regularMarketDayLow", 0.0) or None,
            "open": meta.get("regularMarketOpen", 0.0) or None,
            "prev_close": meta.get("chartPreviousClose", meta.get("previousClose", 0.0)) or None,
            "volume": meta.get("regularMarketVolume", 0) or None,
            "change": meta.get("regularMarketChange", None),
            "change_percent": meta.get("regularMarketChangePercent", None),
            "currency": meta.get("currency", "USD"),
            "exchange": meta.get("exchangeName", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Use the most recent bar timestamp as market_timestamp if available
        timestamps = chart.get("timestamp", [])
        market_ts = datetime.now(timezone.utc)
        if timestamps:
            from datetime import datetime as dt
            market_ts = dt.fromtimestamp(timestamps[-1], tz=timezone.utc)

        return quote, market_ts

    async def _fetch_bars(self, symbol: str, timeframe: str, count: int) -> list[tuple[dict, datetime]]:
        """Fetch historical bars from Yahoo."""
        client = await self._get_client()
        url = YAHOO_CHART_URL.format(symbol=symbol)

        # Map our timeframes to Yahoo intervals
        interval_map = {
            "1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m",
            "1h": "60m", "4h": "60m",  # Yahoo doesn't have 4h, use 60m
            "1D": "1d", "1W": "1wk", "1M": "1mo",
        }
        yahoo_interval = interval_map.get(timeframe, "1m")

        # Range: estimate based on count × interval
        range_map = {
            "1m": "1d", "5m": "5d", "15m": "5d", "30m": "1mo",
            "1h": "1mo", "1D": "1y", "1W": "5y", "1M": "10y",
        }
        yahoo_range = range_map.get(timeframe, "1mo")

        params = {"interval": yahoo_interval, "range": yahoo_range}

        resp = await client.get(url, params=params)
        if resp.status_code != 200:
            raise ProviderError("yahoo", f"HTTP {resp.status_code}", status_code=resp.status_code)

        data = resp.json()
        result = data.get("chart", {}).get("result", [])
        if not result:
            raise ProviderError("yahoo", f"No data for {symbol}")

        chart = result[0]
        timestamps = chart.get("timestamp", [])
        indicators = chart.get("indicators", {})
        quote_data = indicators.get("quote", [{}])[0]

        opens = quote_data.get("open", [])
        highs = quote_data.get("high", [])
        lows = quote_data.get("low", [])
        closes = quote_data.get("close", [])
        volumes = indicators.get("adjclose", [{}])[0].get("adjclose", closes) if "adjclose" in indicators else closes
        vol_data = indicators.get("quote", [{}])[0].get("volume", [])

        bars = []
        for i, ts in enumerate(timestamps):
            if i >= len(closes) or closes[i] is None:
                continue
            bar = {
                "symbol": symbol,
                "timestamp": ts * 1000,  # to millis
                "open": opens[i] if i < len(opens) else None,
                "high": highs[i] if i < len(highs) else None,
                "low": lows[i] if i < len(lows) else None,
                "close": closes[i],
                "volume": vol_data[i] if i < len(vol_data) else 0,
            }
            from datetime import datetime as dt
            bars.append((bar, dt.fromtimestamp(ts, tz=timezone.utc)))
            if len(bars) >= count:
                break

        return bars

    async def close(self) -> None:
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
''')

w("providers/yahoo/tests/__init__.py", "")
w("providers/yahoo/tests/test_adapter.py", '''
"""Tests for Yahoo provider.

These tests use httpx's MockTransport to avoid hitting real Yahoo Finance.
"""
import pytest
import httpx
from datetime import datetime, timezone
from athena_x_provider_yahoo import YahooAdapter


def mock_yahoo_response(symbol: str = "NVDA") -> dict:
    """Build a mock Yahoo chart API response."""
    return {
        "chart": {
            "result": [{
                "meta": {
                    "symbol": symbol,
                    "regularMarketPrice": 128.45,
                    "bid": 128.44,
                    "ask": 128.46,
                    "regularMarketDayHigh": 130.0,
                    "regularMarketDayLow": 127.5,
                    "regularMarketOpen": 129.0,
                    "chartPreviousClose": 127.0,
                    "regularMarketVolume": 5000000,
                    "regularMarketChange": 1.45,
                    "regularMarketChangePercent": 1.14,
                    "currency": "USD",
                    "exchangeName": "NMS",
                },
                "timestamp": [1700000000, 1700000060, 1700000120],
                "indicators": {
                    "quote": [{
                        "open": [129.0, 129.5, 128.5],
                        "high": [130.0, 130.5, 129.0],
                        "low": [128.5, 129.0, 128.0],
                        "close": [129.5, 129.0, 128.45],
                        "volume": [100000, 150000, 200000],
                    }]
                }
            }],
            "error": None
        }
    }


@pytest.fixture
async def mock_provider():
    """Yahoo adapter with mocked HTTP transport."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=mock_yahoo_response("NVDA"))

    transport = httpx.MockTransport(handler)
    p = YahooAdapter()
    # Inject mock client
    p._client = httpx.AsyncClient(
        transport=transport,
        headers={"User-Agent": "test"},
    )
    yield p
    await p.close()


async def test_fetch_quote_parses_yahoo_response(mock_provider):
    result = await mock_provider.fetch_quote("NVDA")
    assert result.provider == "yahoo"
    assert result.data["symbol"] == "NVDA"
    assert result.data["last"] == 128.45
    assert result.data["bid"] == 128.44
    assert result.data["ask"] == 128.46
    assert result.data["volume"] == 5000000
    assert result.latency_ms >= 0


async def test_fetch_quote_archives_raw_payload(tmp_path):
    """Yahoo adapter archives raw payload via RawArchiver."""
    from athena_x_runtime_raw_archival import RawArchiver
    archiver = RawArchiver(base_path=tmp_path)

    def handler(request):
        return httpx.Response(200, json=mock_yahoo_response())

    p = YahooAdapter(archiver=archiver)
    p._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    await p.fetch_quote("NVDA")
    await p.close()

    # Verify file was archived
    files = list(tmp_path.rglob("*.json"))
    assert len(files) == 1


async def test_fetch_quote_handles_error():
    """HTTP errors raise ProviderError."""
    def handler(request):
        return httpx.Response(404, text="Not Found")

    p = YahooAdapter()
    p._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    from athena_x_provider_base.provider import ProviderError
    with pytest.raises(ProviderError):
        await p.fetch_quote("INVALID")
    await p.close()


async def test_fetch_bars(mock_provider):
    results = await mock_provider._fetch_bars("NVDA", "1m", 3)
    assert len(results) == 3
    bar, ts = results[0]
    assert bar["symbol"] == "NVDA"
    assert bar["close"] == 129.5
    assert bar["open"] == 129.0


async def test_health_check(mock_provider):
    await mock_provider.fetch_quote("NVDA")
    health = await mock_provider.health_check()
    assert health["provider"] == "yahoo"
    assert health["successful_calls"] == 1
    assert health["total_calls"] == 1
''')

# ============================================================================
# 8. CNN PROVIDER — providers/cnn/ (Fear & Greed + news)
# ============================================================================

w("providers/cnn/pyproject.toml", '''
[project]
name = "athena-x-provider-cnn"
version = "0.1.0"
description = "CNN Business provider (Fear & Greed Index + news)"
requires-python = ">=3.11"
dependencies = [
    "athena-x-provider-base",
    "athena-x-runtime-logger",
    "httpx>=0.27.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/athena_x_provider_cnn"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
''')

w("providers/cnn/src/athena_x_provider_cnn/__init__.py", '''
"""CNN provider (Fear & Greed + news)."""
from .adapter import CNNAdapter

__all__ = ["CNNAdapter"]
__version__ = "0.1.0"
''')

w("providers/cnn/src/athena_x_provider_cnn/adapter.py", '''
"""CNN Business provider adapter.

Fetches:
- Fear & Greed Index from production.dataviz.cnn.com
- CNN Business news RSS feed

No API key required.
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any
import xml.etree.ElementTree as ET

import httpx

from athena_x_provider_base.base_adapter import BaseProviderAdapter
from athena_x_provider_base.provider import ProviderError


FEAR_GREED_URL = "https://production.dataviz.cnn.com/forecast/indices/fear-greed-graph/now"
CNN_NEWS_RSS = "https://rss.cnn.com/rss/money_news_international.xml"


class CNNAdapter(BaseProviderAdapter):
    """CNN Business provider."""

    name = "cnn"
    transport = "REST"
    asset_classes = ["news"]

    def __init__(self, api_key: str | None = None, **kwargs):
        super().__init__(api_key=None, **kwargs)
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                headers={"User-Agent": "ATHENA-X/0.1"},
                timeout=httpx.Timeout(10.0, connect=5.0),
            )
        return self._client

    async def fetch_fear_greed(self) -> dict:
        """Fetch the current Fear & Greed Index value."""
        client = await self._get_client()
        resp = await client.get(FEAR_GREED_URL)
        if resp.status_code != 200:
            raise ProviderError("cnn", f"HTTP {resp.status_code}", status_code=resp.status_code)

        data = resp.json()
        # CNN returns {'data': [{'value': 45, 'rating': 'Fear', ...}]}
        fear_greed_data = data.get("data", [])
        if not fear_greed_data:
            raise ProviderError("cnn", "No Fear & Greed data in response")

        latest = fear_greed_data[0]
        return {
            "value": latest.get("value"),
            "classification": latest.get("rating"),
            "timestamp": latest.get("x") or latest.get("timestamp"),
            "source": "cnn",
        }

    async def _fetch_news(self, symbols=None, categories=None, limit=50) -> list[tuple[dict, datetime]]:
        """Fetch CNN Business news from RSS feed."""
        client = await self._get_client()
        resp = await client.get(CNN_NEWS_RSS)
        if resp.status_code != 200:
            raise ProviderError("cnn", f"HTTP {resp.status_code}", status_code=resp.status_code)

        articles = self._parse_rss(resp.text, source="cnn", limit=limit)
        return articles

    def _parse_rss(self, rss_text: str, source: str, limit: int = 50) -> list[tuple[dict, datetime]]:
        """Parse an RSS feed into articles."""
        articles = []
        try:
            root = ET.fromstring(rss_text)
            items = root.findall(".//item")
            for item in items[:limit]:
                title = item.findtext("title", "")
                link = item.findtext("link", "")
                description = item.findtext("description", "")
                pub_date = item.findtext("pubDate", "")

                # Parse pubDate (RFC 822 format: "Wed, 17 Jul 2026 13:45:00 GMT")
                published_at = datetime.now(timezone.utc)
                if pub_date:
                    try:
                        from email.utils import parsedate_to_datetime
                        published_at = parsedate_to_datetime(pub_date)
                        if published_at.tzinfo is None:
                            published_at = published_at.replace(tzinfo=timezone.utc)
                    except Exception:
                        pass

                article = {
                    "id": link or title,  # use URL as ID
                    "source": source,
                    "headline": title,
                    "summary": description,
                    "url": link,
                    "published_at": published_at.isoformat(),
                    "symbols": [],  # symbol extraction is Stage 3 (standardization)
                    "categories": ["news"],
                    "sentiment": None,  # left blank — Stage 10 fills this
                }
                articles.append((article, published_at))
        except ET.ParseError as e:
            raise ProviderError(source, f"RSS parse error: {e}")

        return articles

    async def close(self) -> None:
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
''')

w("providers/cnn/tests/__init__.py", "")
w("providers/cnn/tests/test_adapter.py", '''
"""Tests for CNN provider."""
import pytest
import httpx
from athena_x_provider_cnn import CNNAdapter


def mock_fear_greed_response() -> dict:
    return {
        "data": [{
            "value": 45,
            "rating": "Fear",
            "x": 1700000000,
        }]
    }


def mock_cnn_rss() -> str:
    return """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
    <channel>
        <title>CNNMoney</title>
        <item>
            <title>NVDA beats Q3 estimates</title>
            <link>https://example.com/article1</link>
            <description>Nvidia reported strong earnings.</description>
            <pubDate>Wed, 17 Jul 2026 13:45:00 GMT</pubDate>
        </item>
        <item>
            <title>Fed signals rate cut</title>
            <link>https://example.com/article2</link>
            <description>The Federal Reserve indicated a possible rate cut.</description>
            <pubDate>Wed, 17 Jul 2026 14:00:00 GMT</pubDate>
        </item>
    </channel>
</rss>"""


@pytest.fixture
async def provider():
    def handler(request):
        url = str(request.url)
        if "fear-greed" in url:
            return httpx.Response(200, json=mock_fear_greed_response())
        elif "rss" in url:
            return httpx.Response(200, text=mock_cnn_rss())
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    p = CNNAdapter()
    p._client = httpx.AsyncClient(transport=transport)
    yield p
    await p.close()


async def test_fetch_fear_greed(provider):
    result = await provider.fetch_fear_greed()
    assert result["value"] == 45
    assert result["classification"] == "Fear"
    assert result["source"] == "cnn"


async def test_fetch_news_parses_rss(provider):
    articles = await provider._fetch_news(limit=10)
    assert len(articles) == 2
    article, ts = articles[0]
    assert article["headline"] == "NVDA beats Q3 estimates"
    assert article["url"] == "https://example.com/article1"
    assert article["source"] == "cnn"
    assert article["sentiment"] is None  # left blank in Stage 2


async def test_news_articles_have_timestamps(provider):
    articles = await provider._fetch_news(limit=10)
    for article, ts in articles:
        assert ts is not None
        assert ts.year == 2026
''')

# ============================================================================
# 9. FINNHUB PROVIDER — providers/finnhub/ (real impl)
# ============================================================================

w("providers/finnhub/pyproject.toml", '''
[project]
name = "athena-x-provider-finnhub"
version = "0.1.0"
description = "Finnhub provider adapter (REST + WebSocket)"
requires-python = ">=3.11"
dependencies = [
    "athena-x-provider-base",
    "athena-x-runtime-logger",
    "httpx>=0.27.0",
    "websockets>=13.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/athena_x_provider_finnhub"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
''')

w("providers/finnhub/src/athena_x_provider_finnhub/__init__.py", '''
"""Finnhub provider."""
from .adapter import FinnhubAdapter

__all__ = ["FinnhubAdapter"]
__version__ = "0.1.0"
''')

w("providers/finnhub/src/athena_x_provider_finnhub/adapter.py", '''
"""Finnhub provider adapter.

Uses Finnhub's REST API for quotes, company news, and earnings calendar.
WebSocket support for real-time trades is available but optional.

Requires FINNHUB_API_KEY environment variable.
"""
from __future__ import annotations
import os
from datetime import datetime, timezone
from typing import Any

import httpx

from athena_x_provider_base.base_adapter import BaseProviderAdapter
from athena_x_provider_base.provider import ProviderError


FINNHUB_BASE_URL = "https://finnhub.io/api/v1"


class FinnhubAdapter(BaseProviderAdapter):
    """Finnhub provider adapter.

    Layer 1 — Provider Adapters.
    """

    name = "finnhub"
    transport = "REST"
    asset_classes = ["equity", "etf", "currency"]

    def __init__(self, api_key: str | None = None, **kwargs):
        super().__init__(api_key=api_key, **kwargs)
        self._client: httpx.AsyncClient | None = None

    @property
    def _api_key(self) -> str:
        if not self.api_key:
            raise ProviderError("finnhub", "FINNHUB_API_KEY not set")
        return self.api_key

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                headers={"X-Finnhub-Token": self._api_key},
                timeout=httpx.Timeout(10.0, connect=5.0),
            )
        return self._client

    async def _fetch_quote(self, symbol: str) -> tuple[dict, datetime]:
        """Fetch a quote from Finnhub's /quote endpoint."""
        client = await self._get_client()
        url = f"{FINNHUB_BASE_URL}/quote"
        params = {"symbol": symbol, "token": self._api_key}

        resp = await client.get(url, params=params)
        if resp.status_code != 200:
            raise ProviderError("finnhub", f"HTTP {resp.status_code}: {resp.text[:200]}",
                                status_code=resp.status_code)

        data = resp.json()
        # Finnhub returns: {c: current, d: change, dp: change_percent,
        #                   h: high, l: low, o: open, pc: prev_close, t: timestamp}
        market_ts = datetime.now(timezone.utc)
        if data.get("t"):
            market_ts = datetime.fromtimestamp(data["t"], tz=timezone.utc)

        quote = {
            "symbol": symbol,
            "last": data.get("c", 0.0),
            "high": data.get("h"),
            "low": data.get("l"),
            "open": data.get("o"),
            "prev_close": data.get("pc"),
            "change": data.get("d"),
            "change_percent": data.get("dp"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "market_timestamp": market_ts.isoformat(),
        }
        return quote, market_ts

    async def _fetch_news(self, symbols=None, categories=None, limit=50) -> list[tuple[dict, datetime]]:
        """Fetch company news from Finnhub."""
        client = await self._get_client()
        from datetime import date, timedelta

        today = date.today()
        week_ago = today - timedelta(days=7)

        if symbols:
            # Company-specific news
            symbol = symbols[0]
            url = f"{FINNHUB_BASE_URL}/company-news"
            params = {
                "symbol": symbol,
                "from": week_ago.isoformat(),
                "to": today.isoformat(),
                "token": self._api_key,
            }
        else:
            # Market news
            url = f"{FINNHUB_BASE_URL}/news"
            params = {"category": "general", "token": self._api_key}

        resp = await client.get(url, params=params)
        if resp.status_code != 200:
            raise ProviderError("finnhub", f"HTTP {resp.status_code}", status_code=resp.status_code)

        data = resp.json()
        articles = []
        for item in data[:limit]:
            pub_ts = datetime.fromtimestamp(item.get("datetime", 0), tz=timezone.utc)
            article = {
                "id": str(item.get("id", "")),
                "source": "finnhub",
                "headline": item.get("headline", ""),
                "summary": item.get("summary", ""),
                "url": item.get("url", ""),
                "published_at": pub_ts.isoformat(),
                "symbols": [item.get("related", "")] if item.get("related") else [],
                "categories": ["news"],
                "sentiment": None,
            }
            articles.append((article, pub_ts))
        return articles

    async def fetch_company_news(self, symbol: str, days_back: int = 7) -> list[tuple[dict, datetime]]:
        """Convenience method for fetching company-specific news."""
        return await self._fetch_news(symbols=[symbol])

    async def close(self) -> None:
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
''')

w("providers/finnhub/tests/__init__.py", "")
w("providers/finnhub/tests/test_adapter.py", '''
"""Tests for Finnhub provider."""
import pytest
import httpx
from athena_x_provider_finnhub import FinnhubAdapter


def mock_finnhub_quote() -> dict:
    return {
        "c": 128.45,
        "d": 1.45,
        "dp": 1.14,
        "h": 130.0,
        "l": 127.5,
        "o": 129.0,
        "pc": 127.0,
        "t": 1700000000,
    }


@pytest.fixture
async def provider():
    def handler(request):
        return httpx.Response(200, json=mock_finnhub_quote())

    p = FinnhubAdapter(api_key="test-key")
    p._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    yield p
    await p.close()


async def test_fetch_quote(provider):
    result = await provider.fetch_quote("NVDA")
    assert result.provider == "finnhub"
    assert result.data["symbol"] == "NVDA"
    assert result.data["last"] == 128.45
    assert result.data["change"] == 1.45
    assert result.data["change_percent"] == 1.14


async def test_api_key_required():
    """Provider raises if no API key is set."""
    p = FinnhubAdapter(api_key=None)
    from athena_x_provider_base.provider import ProviderError
    with pytest.raises(ProviderError):
        await p.fetch_quote("NVDA")


async def test_http_error_raises(provider):
    """HTTP errors raise ProviderError."""
    def handler(request):
        return httpx.Response(500, text="Internal Server Error")
    provider = FinnhubAdapter(api_key="test")
    provider._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    from athena_x_provider_base.provider import ProviderError
    with pytest.raises(ProviderError):
        await provider.fetch_quote("NVDA")
    await provider.close()
''')

# ============================================================================
# 10. PROVIDER FAILOVER CHAIN — providers/failover/
# ============================================================================

w("providers/failover/pyproject.toml", '''
[project]
name = "athena-x-provider-failover"
version = "0.1.0"
description = "Provider failover chain: Yahoo → Finnhub → Polygon → FlashAlpha → FRED → AlphaVantage"
requires-python = ">=3.11"
dependencies = [
    "athena-x-provider-base",
    "athena-x-runtime-logger",
    "athena-x-runtime-event-bus",
    "athena-x-runtime-institutional-metadata",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/athena_x_provider_failover"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
''')

w("providers/failover/src/athena_x_provider_failover/__init__.py", '''
"""Provider failover chain."""
from .chain import FailoverChain, FailoverResult

__all__ = ["FailoverChain", "FailoverResult"]
__version__ = "0.1.0"
''')

w("providers/failover/src/athena_x_provider_failover/chain.py", '''
"""Provider failover chain — Stage 2 req 1.

Order: Yahoo → Finnhub → Polygon → FlashAlpha → FRED → AlphaVantage

On failure, automatically tries the next provider. If all fail, raises
the last error. Each failover is published as a market:provider-failed-over
event on the bus.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from athena_x_provider_base.provider import ProviderError, ProviderResult, MarketDataProvider
from athena_x_runtime_logger import get_logger

log = get_logger("providers.failover")


@dataclass
class FailoverResult:
    """Result of a failover chain attempt."""
    result: ProviderResult
    provider_used: str
    attempts: list[tuple[str, str | None]]  # [(provider_name, error_or_None), ...]
    failed_over: bool


class FailoverChain:
    """Provider failover chain.

    Usage:
        chain = FailoverChain(
            providers=[yahoo, finnhub, polygon, flashalpha, fred, alphavantage],
            bus=bus,
        )
        result = await chain.fetch_quote("NVDA")
        # result.provider_used might be 'yahoo' or 'finnhub' (if yahoo failed)
    """

    def __init__(
        self,
        providers: list[MarketDataProvider],
        bus=None,
    ):
        self._providers = providers
        self._bus = bus
        self._failover_counts: dict[str, int] = {p.name: 0 for p in providers}

    async def fetch_quote(self, symbol: str) -> FailoverResult:
        """Try each provider in order until one succeeds."""
        attempts: list[tuple[str, str | None]] = []
        last_error: Exception | None = None

        for i, provider in enumerate(self._providers):
            try:
                result = await provider.fetch_quote(symbol)
                attempts.append((provider.name, None))

                # If we failed over (i > 0), publish event
                if i > 0 and self._bus is not None:
                    await self._publish_failover(
                        from_provider=self._providers[0].name,
                        to_provider=provider.name,
                        reason=str(last_error) if last_error else "unknown",
                    )

                return FailoverResult(
                    result=result,
                    provider_used=provider.name,
                    attempts=attempts,
                    failed_over=i > 0,
                )
            except (ProviderError, Exception) as e:
                attempts.append((provider.name, str(e)))
                last_error = e
                log.warning("provider_failed",
                            provider=provider.name,
                            symbol=symbol,
                            error=str(e))
                self._failover_counts[provider.name] += 1
                continue

        # All providers failed
        raise ProviderError(
            "failover-chain",
            f"All providers failed for {symbol}. Last error: {last_error}",
        )

    async def _publish_failover(
        self,
        from_provider: str,
        to_provider: str,
        reason: str,
    ) -> None:
        """Publish a market:provider-failed-over event."""
        if self._bus is None:
            return
        from athena_x_runtime_event_bus import BusEvent
        event = BusEvent.create(
            event_type="market:provider-failed-over",
            provider=to_provider,
            agent_id="providers.failover",
            payload={
                "from": from_provider,
                "to": to_provider,
                "reason": reason,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            confidence=0.9,
        )
        await self._bus.publish(event)

    def get_failover_stats(self) -> dict[str, int]:
        """Return failover counts per provider."""
        return dict(self._failover_counts)
''')

w("providers/failover/tests/__init__.py", "")
w("providers/failover/tests/test_chain.py", '''
"""Tests for provider failover chain (Stage 2 req 1)."""
import pytest
from athena_x_provider_base.provider import ProviderError, ProviderResult
from athena_x_provider_simulated import SimulatedAdapter
from athena_x_provider_failover import FailoverChain
from athena_x_runtime_event_bus import InMemoryBusClient, BusEvent
from datetime import datetime, timezone


class FailingProvider:
    """Provider that always fails — for testing failover."""
    name = "failing"
    transport = "test"
    asset_classes = ["equity"]

    async def fetch_quote(self, symbol):
        raise ProviderError("failing", f"intentional failure for {symbol}")

    async def health_check(self):
        return {"provider": "failing", "connection": "disconnected"}


@pytest.fixture
async def bus():
    b = InMemoryBusClient()
    yield b
    await b.close()


async def test_failover_to_next_provider_on_failure(bus):
    """If the first provider fails, the chain tries the next."""
    failing = FailingProvider()
    simulated = SimulatedAdapter(seed=42)
    chain = FailoverChain(providers=[failing, simulated], bus=bus)

    result = await chain.fetch_quote("NVDA")

    assert result.provider_used == "simulated"
    assert result.failed_over is True
    assert len(result.attempts) == 2
    assert result.attempts[0][0] == "failing"
    assert result.attempts[0][1] is not None  # error message
    assert result.attempts[1][0] == "simulated"
    assert result.attempts[1][1] is None  # success


async def test_no_failover_when_first_succeeds(bus):
    """If the first provider succeeds, no failover occurs."""
    simulated = SimulatedAdapter(seed=42)
    chain = FailoverChain(providers=[simulated], bus=bus)

    result = await chain.fetch_quote("NVDA")
    assert result.provider_used == "simulated"
    assert result.failed_over is False


async def test_failover_publishes_event(bus):
    """Failover publishes market:provider-failed-over event."""
    received_events = []

    async def handler(event):
        received_events.append(event)

    await bus.subscribe("market:provider-failed-over", handler)

    failing = FailingProvider()
    simulated = SimulatedAdapter(seed=42)
    chain = FailoverChain(providers=[failing, simulated], bus=bus)

    await chain.fetch_quote("NVDA")

    assert len(received_events) == 1
    event = received_events[0]
    assert event.event_type == "market:provider-failed-over"
    assert event.payload["from"] == "failing"
    assert event.payload["to"] == "simulated"


async def test_all_providers_fail_raises(bus):
    """If all providers fail, the chain raises."""
    failing1 = FailingProvider()
    failing1.name = "failing1"
    failing2 = FailingProvider()
    failing2.name = "failing2"

    chain = FailoverChain(providers=[failing1, failing2], bus=bus)

    with pytest.raises(ProviderError):
        await chain.fetch_quote("NVDA")


async def test_failover_stats_tracked(bus):
    """Chain tracks failover counts per provider."""
    failing = FailingProvider()
    simulated = SimulatedAdapter(seed=42)
    chain = FailoverChain(providers=[failing, simulated], bus=bus)

    await chain.fetch_quote("NVDA")
    await chain.fetch_quote("SPY")

    stats = chain.get_failover_stats()
    assert stats["failing"] == 2  # failed twice
    assert stats["simulated"] == 0  # never failed
''')

print(f"\n✅ Stage 2 Part 1 complete: {len(FILES)} files written")
print("\nComponents implemented:")
print("  1. runtime/institutional-metadata/  — 10 mandatory fields per record")
print("  2. runtime/session-awareness/       — overnight/pre/regular/post/weekend/holiday")
print("  3. runtime/raw-archival/            — provider/yyyy/mm/dd/hh/ structure")
print("  4. runtime/data-freshness/          — fresh/delayed/stale tracking")
print("  5. providers/base/                  — MarketDataProvider protocol")
print("  6. providers/simulated/             — dev-only simulated provider")
print("  7. providers/yahoo/                 — Yahoo Finance (real impl)")
print("  8. providers/finnhub/               — Finnhub (real impl)")
print("  9. providers/cnn/                   — CNN Fear & Greed + news RSS")
print(" 10. providers/failover/              — failover chain with event publishing")
print("\nNext: install deps and run tests")
