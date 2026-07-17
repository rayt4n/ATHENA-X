"""WebSocket bridge - Stage 6 req 9.

Mirrors backend events to frontend in real time.

- Frontend subscribes via WebSocket
- Pattern-based subscriptions (e.g., market:*, ai:forecast)
- Backpressure: drop stale market data >500ms on frontend side
- Connection management (auto-reconnect)
"""
from __future__ import annotations
import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import RLock
from typing import Any
from uuid import UUID, uuid4

from athena_x_runtime_event_envelope import EventEnvelope, EventPriority
from athena_x_runtime_logger import get_logger

log = get_logger("runtime.websocket-bridge")


@dataclass
class ClientSubscription:
    """A frontend client's subscription."""
    client_id: str
    patterns: list[str]  # e.g., ["market:*", "ai:forecast"]
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class WebSocketClient:
    """Represents a connected frontend client."""

    def __init__(self, client_id: str):
        self.client_id = client_id
        self.subscriptions: list[str] = []
        self.queue: asyncio.Queue = asyncio.Queue(maxsize=1000)
        self.connected = True
        self.events_sent = 0
        self.events_dropped = 0

    async def send(self, event: EventEnvelope) -> bool:
        """Send an event to this client. Returns False if dropped (queue full)."""
        if not self.connected:
            return False
        try:
            self.queue.put_nowait(event)
            self.events_sent += 1
            return True
        except asyncio.QueueFull:
            # Drop oldest market data to make room
            if event.priority in (EventPriority.HIGH, EventPriority.NORMAL):
                try:
                    self.queue.get_nowait()  # drop oldest
                    self.queue.put_nowait(event)
                    self.events_dropped += 1
                    return True
                except asyncio.QueueEmpty:
                    return False
            self.events_dropped += 1
            return False

    async def receive(self, timeout: float | None = None) -> EventEnvelope | None:
        """Receive the next event for this client."""
        try:
            if timeout:
                return await asyncio.wait_for(self.queue.get(), timeout=timeout)
            return self.queue.get_nowait()
        except (asyncio.TimeoutError, asyncio.QueueEmpty):
            return None

    def matches(self, event: EventEnvelope) -> bool:
        """Check if the client is subscribed to this event type."""
        if not self.subscriptions:
            return True  # subscribed to all
        for pattern in self.subscriptions:
            if self._matches_pattern(pattern, event.event_type):
                return True
        return False

    def _matches_pattern(self, pattern: str, event_type: str) -> bool:
        """Glob pattern match."""
        if pattern == "*":
            return True
        if "*" not in pattern:
            return pattern == event_type
        prefix = pattern.split("*")[0]
        return event_type.startswith(prefix)


class WebSocketBridge:
    """Bridges backend events to frontend WebSocket clients.

    Usage:
        bridge = WebSocketBridge()
        client = bridge.add_client("client-1")
        bridge.subscribe("client-1", ["market:*", "ai:forecast"])

        # When backend publishes an event:
        await bridge.broadcast(event)

        # Frontend receives:
        event = await client.receive()
    """

    def __init__(self, max_clients: int = 10000):
        self._clients: dict[str, WebSocketClient] = {}
        self._lock = RLock()
        self._max_clients = max_clients
        self._total_broadcast = 0
        self._total_dropped = 0

    def add_client(self, client_id: str | None = None) -> WebSocketClient:
        """Add a new frontend client."""
        cid = client_id or str(uuid4())
        with self._lock:
            if len(self._clients) >= self._max_clients:
                raise RuntimeError("Max clients reached")
            client = WebSocketClient(client_id=cid)
            self._clients[cid] = client
        log.info("ws_client_connected", client_id=cid)
        return client

    def remove_client(self, client_id: str) -> None:
        """Remove a frontend client."""
        with self._lock:
            client = self._clients.pop(client_id, None)
            if client:
                client.connected = False
        log.info("ws_client_disconnected", client_id=client_id)

    def subscribe(self, client_id: str, patterns: list[str]) -> None:
        """Subscribe a client to event patterns."""
        with self._lock:
            client = self._clients.get(client_id)
            if client:
                client.subscriptions = patterns

    async def broadcast(self, event: EventEnvelope) -> int:
        """Broadcast an event to all subscribed clients.

        Returns the number of clients that received the event.
        """
        self._total_broadcast += 1
        delivered = 0

        with self._lock:
            clients = list(self._clients.values())

        for client in clients:
            if not client.connected:
                continue
            if not client.matches(event):
                continue
            success = await client.send(event)
            if success:
                delivered += 1
            else:
                self._total_dropped += 1

        return delivered

    def get_stats(self) -> dict:
        """Get bridge statistics."""
        with self._lock:
            return {
                "connected_clients": len(self._clients),
                "total_broadcasts": self._total_broadcast,
                "total_dropped": self._total_dropped,
                "clients": [
                    {
                        "client_id": c.client_id,
                        "subscriptions": c.subscriptions,
                        "events_sent": c.events_sent,
                        "events_dropped": c.events_dropped,
                    }
                    for c in self._clients.values()
                ],
            }
