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
