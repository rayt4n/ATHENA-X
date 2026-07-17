"""Redis Pub/Sub implementation of BusClient."""
from __future__ import annotations
import json
from typing import Awaitable, Callable
import redis.asyncio as redis
from .types import BusEvent, BusClient


class RedisBusClient(BusClient):
    def __init__(self, redis_url: str):
        self._redis_url = redis_url
        self._pubsub: redis.Redis | None = None
        self._handlers: dict[str, list[Callable[[BusEvent], Awaitable[None]]]] = {}

    async def connect(self) -> None:
        self._pubsub = redis.from_url(self._redis_url)

    async def publish(self, event: BusEvent) -> None:
        if self._pubsub is None:
            raise RuntimeError("Bus not connected")
        channel = event.event_type
        await self._pubsub.publish(channel, event.model_dump_json())

    async def subscribe(self, pattern: str, handler) -> None:
        if self._pubsub is None:
            raise RuntimeError("Bus not connected")
        self._handlers.setdefault(pattern, []).append(handler)
        await self._pubsub.psubscribe(pattern)

    async def close(self) -> None:
        if self._pubsub is not None:
            await self._pubsub.close()
            self._pubsub = None
