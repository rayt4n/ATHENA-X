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
