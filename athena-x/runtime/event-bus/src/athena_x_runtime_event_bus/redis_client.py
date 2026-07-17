"""Redis Pub/Sub implementation of BusClient."""
from __future__ import annotations
import asyncio
import json
from typing import Set
import time

try:
    import redis.asyncio as aioredis
    from redis.asyncio import Redis
except ImportError:
    aioredis = None
    Redis = None

from .types import BusEvent, BusClient, EventHandler, pattern_matches
from athena_x_runtime_logger import get_logger

log = get_logger("runtime.event-bus.redis")


class RedisBusClient(BusClient):
    """Redis Pub/Sub bus client.

    Uses Redis PUBLISH for fan-out and SUBSCRIBE for receiving.
    Pattern subscriptions use PSUBSCRIBE with glob patterns.
    """

    def __init__(self, redis_url: str = "redis://localhost:6379",
                 backpressure_max_age_ms: int = 500):
        if aioredis is None:
            raise ImportError("redis package not installed. Run: pip install redis")
        self._redis_url = redis_url
        self._backpressure_max_age_ms = backpressure_max_age_ms
        self._redis: Redis | None = None
        self._pubsub = None
        self._handlers: dict[str, set[EventHandler]] = {}
        self._listener_task: asyncio.Task | None = None
        self._closed = False
        self._publish_count = 0
        self._drop_count = 0

    async def connect(self) -> None:
        """Connect to Redis. Must be called before publish/subscribe."""
        self._redis = aioredis.from_url(
            self._redis_url,
            encoding="utf-8",
            decode_responses=True,
            socket_keepalive=True,
            socket_connect_timeout=5,
            retry_on_timeout=True,
        )
        # Test connection
        await self._redis.ping()
        self._pubsub = self._redis.pubsub()
        log.info("redis_bus_connected", url=self._redis_url)

    async def publish(self, event: BusEvent) -> None:
        if self._closed or self._redis is None:
            raise RuntimeError("Bus not connected. Call connect() first.")

        # Backpressure
        if (event.event_type.startswith("market:")
                and self._backpressure_max_age_ms > 0):
            age_ms = (time.time() - event.timestamp.timestamp()) * 1000
            if age_ms > self._backpressure_max_age_ms:
                self._drop_count += 1
                return

        channel = event.event_type
        message = event.model_dump_json(by_alias=True)
        await self._redis.publish(channel, message)
        self._publish_count += 1

    async def subscribe(self, pattern: str, handler: EventHandler) -> None:
        if self._pubsub is None:
            raise RuntimeError("Bus not connected. Call connect() first.")
        self._handlers.setdefault(pattern, set()).add(handler)
        # Use PSUBSCRIBE for glob patterns, SUBSCRIBE for exact channels
        if "*" in pattern:
            await self._pubsub.psubscribe(pattern)
        else:
            await self._pubsub.subscribe(pattern)
        # Start listener if not running
        if self._listener_task is None:
            self._listener_task = asyncio.create_task(self._listen())

    async def unsubscribe(self, pattern: str, handler: EventHandler) -> None:
        if pattern in self._handlers:
            self._handlers[pattern].discard(handler)
            if not self._handlers[pattern]:
                del self._handlers[pattern]
                if self._pubsub is not None:
                    if "*" in pattern:
                        await self._pubsub.punsubscribe(pattern)
                    else:
                        await self._pubsub.unsubscribe(pattern)

    async def _listen(self) -> None:
        """Listen for messages and dispatch to handlers."""
        if self._pubsub is None:
            return
        try:
            async for message in self._pubsub.listen():
                if message is None:
                    continue
                msg_type = message.get("type")
                if msg_type not in ("message", "pmessage"):
                    continue
                channel = message.get("channel", "")
                data = message.get("data", "")
                if not isinstance(data, str):
                    continue
                try:
                    event = BusEvent.model_validate_json(data)
                except Exception as e:
                    log.error("event_parse_failed", error=str(e), raw=data[:200])
                    continue
                # Dispatch to matching handlers
                for pattern, handlers in list(self._handlers.items()):
                    if pattern_matches(pattern, channel):
                        for h in list(handlers):
                            try:
                                await h(event)
                            except Exception as e:
                                log.error("handler_failed",
                                          error=str(e),
                                          event_type=event.event_type)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            log.error("listener_crashed", error=str(e))

    async def close(self) -> None:
        self._closed = True
        if self._listener_task is not None:
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass
            self._listener_task = None
        if self._pubsub is not None:
            await self._pubsub.close()
            self._pubsub = None
        if self._redis is not None:
            await self._redis.close()
            self._redis = None
        log.info("redis_bus_closed")

    async def health_check(self) -> bool:
        if self._redis is None or self._closed:
            return False
        try:
            await self._redis.ping()
            return True
        except Exception:
            return False

    @property
    def publish_count(self) -> int:
        return self._publish_count

    @property
    def drop_count(self) -> int:
        return self._drop_count
