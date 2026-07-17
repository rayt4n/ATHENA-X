"""Cross-market watchlist — 16 synchronized instruments (Stage 2 req 1.4).

Continuously monitors:
  SPY, ES, SPX, NQ, QQQ, DIA, IWM, SOXX
  VIX, VVIX, TNX, DXY
  Gold, Oil, Copper, USDJPY

This ensures downstream correlation engines (Stage 9) have synchronized inputs.
"""
from __future__ import annotations
import asyncio
from datetime import datetime, timezone
from typing import Any

from athena_x_runtime_event_bus import BusClient, BusEvent
from athena_x_runtime_logger import get_logger
from athena_x_collector_base import CollectorConfig, CollectorRegistry
from athena_x_collector_market_data import MarketDataCollector, MARKET_DATA_CONFIGS
from athena_x_provider_failover import FailoverChain

log = get_logger("collectors.cross-market")


CROSS_MARKET_SYMBOLS = [
    "SPY", "ES", "SPX", "NQ", "QQQ", "DIA", "IWM", "SOXX",
    "VIX", "VVIX", "TNX", "DXY",
    "Gold", "Oil", "Copper", "USDJPY",
]


class CrossMarketWatchlist:
    """Manages 16 synchronized market data collectors.

    Each instrument has its own MarketDataCollector running at its natural
    frequency. The watchlist ensures all 16 are running and publishes a
    cross-market snapshot event every minute.
    """

    def __init__(
        self,
        failover_chain: FailoverChain,
        bus: BusClient,
        registry: CollectorRegistry | None = None,
        snapshot_interval_seconds: int = 60,
    ):
        self._failover_chain = failover_chain
        self._bus = bus
        self._registry = registry or CollectorRegistry()
        self._snapshot_interval = snapshot_interval_seconds
        self._collectors: dict[str, MarketDataCollector] = {}
        self._snapshot_task: asyncio.Task | None = None
        self._running = False
        self._latest_quotes: dict[str, dict] = {}

        # Track quotes for snapshot
        self._setup_quote_subscriber()

    def _setup_quote_subscriber(self) -> None:
        """Subscribe to market:quote-updated to track latest quotes."""
        async def handler(event: BusEvent):
            symbol = event.payload.get("metadata", {}).get("symbol")
            if symbol and symbol in CROSS_MARKET_SYMBOLS:
                self._latest_quotes[symbol] = event.payload.get("data", {})
        # Schedule subscription
        asyncio.ensure_future(self._bus.subscribe("market:quote-updated", handler))

    async def start(self) -> None:
        """Start all 16 collectors + snapshot publisher."""
        if self._running:
            return
        self._running = True

        # Create + start a collector for each symbol
        for symbol in CROSS_MARKET_SYMBOLS:
            config = MARKET_DATA_CONFIGS.get(symbol)
            if config is None:
                log.warning("no_config_for_symbol", symbol=symbol)
                continue
            collector = MarketDataCollector(
                config=config,
                failover_chain=self._failover_chain,
                bus=self._bus,
            )
            self._collectors[symbol] = collector
            self._registry.register(collector)
            await collector.start()

        # Start snapshot publisher
        self._snapshot_task = asyncio.create_task(self._snapshot_loop())
        log.info("cross_market_watchlist_started",
                 symbols=CROSS_MARKET_SYMBOLS,
                 snapshot_interval=self._snapshot_interval)

    async def stop(self) -> None:
        """Stop all collectors."""
        self._running = False
        if self._snapshot_task is not None:
            self._snapshot_task.cancel()
            try:
                await self._snapshot_task
            except asyncio.CancelledError:
                pass
            self._snapshot_task = None

        for collector in self._collectors.values():
            await collector.stop()
        self._collectors.clear()
        log.info("cross_market_watchlist_stopped")

    async def _snapshot_loop(self) -> None:
        """Publish a cross-market snapshot every minute."""
        while self._running:
            try:
                await asyncio.sleep(self._snapshot_interval)
                await self._publish_snapshot()
            except asyncio.CancelledError:
                break
            except Exception as e:
                log.error("snapshot_failed", error=str(e))

    async def _publish_snapshot(self) -> None:
        """Publish cross-market:symbol-state-updated for each symbol."""
        now = datetime.now(timezone.utc)
        for symbol, quote in self._latest_quotes.items():
            event = BusEvent.create(
                event_type="cross-market:symbol-state-updated",
                provider="cross-market-watchlist",
                agent_id="cross-market.watchlist",
                payload={
                    "symbol": symbol,
                    "state": quote,
                    "snapshot_timestamp": now.isoformat(),
                },
                confidence=0.9,
            )
            await self._bus.publish(event)

    def get_status(self) -> dict:
        """Return watchlist status."""
        return {
            "running": self._running,
            "symbols_monitored": len(self._collectors),
            "symbols_with_data": len(self._latest_quotes),
            "expected_symbols": CROSS_MARKET_SYMBOLS,
            "missing_symbols": [
                s for s in CROSS_MARKET_SYMBOLS if s not in self._collectors
            ],
        }
