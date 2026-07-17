"""Market data collector for 20 instruments (Stage 2 req 1.1).

Instruments:
  Primary: ES, SPY, SPX, NQ, QQQ, DIA, IWM, SOXX
  Volatility: VIX, VVIX, MOVE
  Rates & FX: TNX, DXY, USDJPY
  Commodities: Gold, Oil, Copper
  Global: Europe, Asia, Crypto (BTC, ETH)
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any

from athena_x_collector_base import BaseCollector, CollectorConfig
from athena_x_provider_base.provider import MarketDataProvider
from athena_x_provider_failover import FailoverChain


# The 20 instruments and their asset classes
MARKET_DATA_SYMBOLS = [
    # Primary Markets (8)
    ("ES", "future", 1.0),    # main instrument
    ("SPY", "etf", 1.0),
    ("SPX", "index", 1.0),
    ("NQ", "future", 1.0),
    ("QQQ", "etf", 1.0),
    ("DIA", "etf", 5.0),
    ("IWM", "etf", 5.0),
    ("SOXX", "etf", 5.0),
    # Volatility (3)
    ("VIX", "volatility", 15.0),
    ("VVIX", "volatility", 15.0),
    ("MOVE", "volatility", 15.0),
    # Rates & FX (3)
    ("TNX", "yield", 15.0),
    ("DXY", "currency", 5.0),
    ("USDJPY", "currency", 5.0),
    # Commodities (3)
    ("Gold", "commodity", 5.0),
    ("Oil", "commodity", 5.0),
    ("Copper", "commodity", 5.0),
    # Global Markets (3)
    ("Europe", "index", 30.0),
    ("Asia", "index", 30.0),
    ("BTC-USD", "crypto", 5.0),
    ("ETH-USD", "crypto", 5.0),
]


MARKET_DATA_CONFIGS = {
    symbol: CollectorConfig(
        collector_id=f"market-data:{symbol}",
        symbol=symbol,
        asset_class=asset_class,
        poll_interval_seconds=interval,
        expected_frequency_seconds=interval,
    )
    for symbol, asset_class, interval in MARKET_DATA_SYMBOLS
}


class MarketDataCollector(BaseCollector):
    """Market data collector — fetches quotes for a single instrument.

    Layer 1 — Provider Adapters (via FailoverChain).
    Layer 2 — Collector agent (this class).
    """

    def __init__(
        self,
        config: CollectorConfig,
        failover_chain: FailoverChain,
        **kwargs,
    ):
        super().__init__(config=config, **kwargs)
        self._failover_chain = failover_chain

    async def fetch_data(self) -> tuple[dict, datetime]:
        """Fetch a quote via the failover chain."""
        failover_result = await self._failover_chain.fetch_quote(self.symbol)
        provider_result = failover_result.result
        return provider_result.data, provider_result.market_timestamp

    def _get_provider_name(self) -> str:
        """Return the last provider used (best effort)."""
        # The failover chain tracks this — for now, return 'failover-chain'
        # The actual provider is recorded in the metadata via the result
        return "failover-chain"

    def get_event_type(self) -> str:
        return "market:quote-updated"
