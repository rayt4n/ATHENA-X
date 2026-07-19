"""Base collector framework.

A collector is a long-running agent that periodically fetches data from
providers, attaches institutional metadata, archives raw payloads, and
publishes events on the bus.

Layer 1 — Provider Adapters → Layer 2 collector agents.

Stage 2 rule: collectors ONLY download + timestamp + archive + publish.
NO calculations.
"""
from __future__ import annotations
import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from athena_x_runtime_event_bus import BusClient, BusEvent
from athena_x_runtime_logger import get_logger, log_context
from athena_x_runtime_institutional_metadata import (
    create_metadata, InstitutionalMetadata, AssetClass, DataStatus,
)
from athena_x_runtime_session_awareness import SessionDetector, SessionType
from athena_x_runtime_raw_archival import RawArchiver
from athena_x_runtime_data_freshness import FreshnessTracker
from athena_x_runtime_scheduler import Scheduler

log = get_logger("collectors.base")


@dataclass
class CollectorConfig:
    """Configuration for a collector."""
    collector_id: str
    symbol: str
    asset_class: AssetClass | str
    poll_interval_seconds: float = 1.0
    expected_frequency_seconds: float = 1.0
    enabled: bool = True


class BaseCollector:
    """Base class for data collection agents.

    Subclasses implement `fetch_data()` which returns the raw payload.
    The base class handles:
      - Periodic scheduling
      - Institutional metadata attachment
      - Raw archival
      - Freshness tracking
      - Bus event publishing
      - Heartbeat emission
    """

    def __init__(
        self,
        config: CollectorConfig,
        bus: BusClient,
        archiver: RawArchiver | None = None,
        freshness_tracker: FreshnessTracker | None = None,
        session_detector: SessionDetector | None = None,
    ):
        self.config = config
        self._bus = bus
        self._archiver = archiver
        self._freshness = freshness_tracker
        self._session_detector = session_detector or SessionDetector()
        self._running = False
        self._task: asyncio.Task | None = None
        self._collect_count = 0
        self._error_count = 0
        self._last_collect: datetime | None = None

        # Register stream for freshness tracking
        if self._freshness is not None:
            stream_id = f"{self.collector_id}:{config.symbol}"
            self._freshness.register_stream(
                stream_id,
                expected_frequency_s=config.expected_frequency_seconds,
            )

    @property
    def collector_id(self) -> str:
        return self.config.collector_id

    @property
    def symbol(self) -> str:
        return self.config.symbol

    async def fetch_data(self) -> tuple[Any, datetime]:
        """Fetch raw data. Subclasses MUST implement.

        Returns:
            (raw_payload, market_timestamp)
        """
        raise NotImplementedError

    def get_event_type(self) -> str:
        """Bus event type for this collector's data. Override in subclasses."""
        return "market:quote-updated"

    def get_asset_class(self) -> AssetClass:
        if isinstance(self.config.asset_class, str):
            return AssetClass(self.config.asset_class)
        return self.config.asset_class

    async def start(self) -> None:
        """Start periodic collection."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        log.info("collector_started",
                 collector_id=self.collector_id,
                 symbol=self.symbol,
                 poll_interval=self.config.poll_interval_seconds)

        # Publish agent-started event
        await self._publish_system_event("system:agent-started", {
            "agentId": self.collector_id,
            "moduleId": "data-collection",
            "version": "0.1.0",
        })

    async def stop(self) -> None:
        """Stop collection."""
        self._running = False
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        log.info("collector_stopped", collector_id=self.collector_id)

        await self._publish_system_event("system:agent-stopped", {
            "agentId": self.collector_id,
            "reason": "graceful_shutdown",
        })

    async def _run_loop(self) -> None:
        """Main collection loop."""
        while self._running:
            try:
                await self.collect_once()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._error_count += 1
                log.error("collection_failed",
                          collector_id=self.collector_id,
                          error=str(e))
            await asyncio.sleep(self.config.poll_interval_seconds)

    async def collect_once(self) -> Any:
        """Fetch data once, attach metadata, archive, and publish."""
        start = time.monotonic()
        try:
            raw_payload, market_ts = await self.fetch_data()
            latency_ms = int((time.monotonic() - start) * 1000)

            # Detect trading session
            session_info = self._session_detector.detect(market_ts, symbol=self.symbol)

            # Build institutional metadata
            metadata = create_metadata(
                provider=self._get_provider_name(),
                symbol=self.symbol,
                asset_class=self.get_asset_class(),
                market_timestamp=market_ts,
                provider_latency_ms=latency_ms,
                session=session_info.session.value,
                status=DataStatus.FRESH,
            )

            # Archive raw payload
            if self._archiver is not None:
                self._archiver.archive(
                    provider=metadata.provider,
                    payload=raw_payload,
                    timestamp=metadata.download_timestamp,
                )

            # Track freshness
            if self._freshness is not None:
                stream_id = f"{self.collector_id}:{self.symbol}"
                self._freshness.record_receipt(stream_id)

            # Publish bus event
            event = BusEvent.create(
                event_type=self.get_event_type(),
                provider=metadata.provider,
                agent_id=self.collector_id,
                payload={
                    "metadata": metadata.model_dump(by_alias=True),
                    "data": raw_payload,
                },
                confidence=metadata.confidence_score,
                latency=latency_ms,
                processing_time=latency_ms,
            )
            await self._bus.publish(event)

            self._collect_count += 1
            self._last_collect = datetime.now(timezone.utc)

            # Emit heartbeat
            await self._emit_heartbeat(running=True)

            return raw_payload

        except Exception as e:
            self._error_count += 1
            await self._emit_heartbeat(running=False)
            raise

    def _get_provider_name(self) -> str:
        """Override in subclasses to specify the provider."""
        return "unknown"

    async def _emit_heartbeat(self, running: bool) -> None:
        """Emit system:agent-heartbeat event."""
        event = BusEvent.create(
            event_type="system:agent-heartbeat",
            provider=self.collector_id,
            agent_id=self.collector_id,
            payload={
                "agentId": self.collector_id,
                "timestamp": int(datetime.now(timezone.utc).timestamp() * 1000),
                "metrics": {
                    "running": running,
                    "lastUpdate": self._last_collect.isoformat() if self._last_collect else None,
                    "cpu": 0.0,
                    "memory": 0.0,
                    "apiLatency": 0.0,
                    "queueLength": 0,
                    "errorCount": self._error_count,
                    "restartCount": 0,
                    "confidence": 0.9,
                    "version": "0.1.0",
                }
            },
            confidence=0.9,
        )
        await self._bus.publish(event)

    async def _publish_system_event(self, event_type: str, payload: dict) -> None:
        event = BusEvent.create(
            event_type=event_type,
            provider=self.collector_id,
            agent_id=self.collector_id,
            payload=payload,
        )
        await self._bus.publish(event)

    def get_stats(self) -> dict:
        """Return collector statistics."""
        return {
            "collector_id": self.collector_id,
            "symbol": self.symbol,
            "running": self._running,
            "collect_count": self._collect_count,
            "error_count": self._error_count,
            "last_collect": self._last_collect.isoformat() if self._last_collect else None,
        }
