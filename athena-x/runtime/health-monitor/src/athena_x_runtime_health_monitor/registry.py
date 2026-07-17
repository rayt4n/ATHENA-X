"""Health registry — tracks current health state of all agents + providers."""
from __future__ import annotations
from datetime import datetime, timezone, timedelta
from threading import Lock
from typing import Iterator
from .types import AgentHealth, ProviderHealth


class HealthRegistry:
    """Thread-safe registry of agent + provider health states.

    Updated when heartbeats arrive. Queried by the dashboard + supervisor.
    """

    def __init__(self, heartbeat_miss_threshold: int = 3,
                 heartbeat_interval_seconds: int = 5):
        self._agents: dict[str, AgentHealth] = {}
        self._providers: dict[str, ProviderHealth] = {}
        self._lock = Lock()
        self._heartbeat_miss_threshold = heartbeat_miss_threshold
        self._heartbeat_interval_seconds = heartbeat_interval_seconds

    def update_agent(self, health: AgentHealth) -> None:
        with self._lock:
            self._agents[health.agent_id] = health

    def update_provider(self, health: ProviderHealth) -> None:
        with self._lock:
            self._providers[health.provider] = health

    def get_agent(self, agent_id: str) -> AgentHealth | None:
        with self._lock:
            health = self._agents.get(agent_id)
            if health is None:
                return None
            # Check staleness — if last_update is too old, mark as not running
            if health.last_update:
                age = (datetime.now(timezone.utc) - health.last_update).total_seconds()
                threshold = self._heartbeat_interval_seconds * self._heartbeat_miss_threshold
                if age > threshold:
                    return health.model_copy(update={"running": False})
            return health

    def get_provider(self, provider: str) -> ProviderHealth | None:
        with self._lock:
            return self._providers.get(provider)

    def list_agents(self) -> list[AgentHealth]:
        """All agents, with staleness check applied."""
        with self._lock:
            ids = list(self._agents.keys())
        return [h for h in (self.get_agent(aid) for aid in ids) if h is not None]

    def list_providers(self) -> list[ProviderHealth]:
        with self._lock:
            return list(self._providers.values())

    def list_failing_agents(self) -> list[AgentHealth]:
        """Agents that are not running (missed heartbeats)."""
        return [a for a in self.list_agents() if not a.running]

    def list_degraded_providers(self) -> list[ProviderHealth]:
        """Providers with connection != 'connected'."""
        return [p for p in self.list_providers() if p.connection != "connected"]

    def clear(self) -> None:
        with self._lock:
            self._agents.clear()
            self._providers.clear()

    def __iter__(self) -> Iterator[AgentHealth]:
        return iter(self.list_agents())
