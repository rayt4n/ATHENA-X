"""Health monitor — subscribes to heartbeat events, updates registry."""
from __future__ import annotations
import asyncio
from datetime import datetime, timezone

from athena_x_runtime_event_bus import BusClient, BusEvent
from athena_x_runtime_logger import get_logger, log_context
from .registry import HealthRegistry
from .types import AgentHealth, ProviderHealth

log = get_logger("runtime.health-monitor")


class HealthMonitor:
    """Subscribes to system:agent-heartbeat + system:provider-health-updated
    events and updates the HealthRegistry.

    Also emits supervisor:agent-failing when an agent misses heartbeats.
    """

    def __init__(
        self,
        bus: BusClient,
        registry: HealthRegistry,
        heartbeat_interval_seconds: int = 5,
        heartbeat_miss_threshold: int = 3,
    ):
        self._bus = bus
        self._registry = registry
        self._heartbeat_interval = heartbeat_interval_seconds
        self._miss_threshold = heartbeat_miss_threshold
        self._checker_task: asyncio.Task | None = None
        self._closed = False

    async def start(self) -> None:
        """Subscribe to heartbeat events + start failure checker."""
        await self._bus.subscribe("system:agent-heartbeat", self._on_agent_heartbeat)
        await self._bus.subscribe("system:provider-health-updated", self._on_provider_health)
        self._checker_task = asyncio.create_task(self._failure_checker())
        log.info("health_monitor_started",
                 heartbeat_interval=self._heartbeat_interval,
                 miss_threshold=self._miss_threshold)

    async def stop(self) -> None:
        self._closed = True
        if self._checker_task is not None:
            self._checker_task.cancel()
            try:
                await self._checker_task
            except asyncio.CancelledError:
                pass
            self._checker_task = None
        log.info("health_monitor_stopped")

    async def _on_agent_heartbeat(self, event: BusEvent) -> None:
        """Handle system:agent-heartbeat event."""
        try:
            metrics = event.payload.get("metrics", {})
            # Parse timestamp — accept unix-millis (int), unix-seconds (float),
            # ISO string, or fall back to event.timestamp.
            ts_value = event.payload.get("timestamp")
            last_update = datetime.now(timezone.utc)
            if isinstance(ts_value, (int, float)):
                # If value is > 1e12, it's milliseconds; otherwise seconds
                seconds = ts_value / 1000 if ts_value > 1e12 else ts_value
                last_update = datetime.fromtimestamp(seconds, tz=timezone.utc)
            elif isinstance(ts_value, str):
                last_update = datetime.fromisoformat(ts_value.replace("Z", "+00:00"))
            else:
                last_update = event.timestamp

            health = AgentHealth(
                agentId=event.payload.get("agentId") or event.agent_id,
                running=metrics.get("running", True),
                lastUpdate=last_update,
                cpu=metrics.get("cpu", 0.0),
                memory=metrics.get("memory", 0.0),
                apiLatency=metrics.get("apiLatency", 0.0),
                queueLength=metrics.get("queueLength", 0),
                errorCount=metrics.get("errorCount", 0),
                restartCount=metrics.get("restartCount", 0),
                confidence=metrics.get("confidence", 1.0),
                version=metrics.get("version", "0.1.0"),
            )
            self._registry.update_agent(health)
        except Exception as e:
            log.error("heartbeat_parse_failed", error=str(e), event_id=str(event.event_id))

    async def _on_provider_health(self, event: BusEvent) -> None:
        """Handle system:provider-health-updated event."""
        try:
            payload = event.payload
            health = ProviderHealth(
                provider=payload.get("provider", ""),
                connection=payload.get("status", "disconnected"),
                delay=payload.get("delay", 0.0),
                missingBars=payload.get("missingBars", 0),
                missingTicks=payload.get("missingTicks", 0),
                apiErrors=payload.get("apiErrors", 0),
                failoverCount=payload.get("failoverCount", 0),
                freshness=payload.get("freshness", 0.0),
                reliabilityScore=payload.get("reliabilityScore", 1.0),
            )
            self._registry.update_provider(health)
        except Exception as e:
            log.error("provider_health_parse_failed", error=str(e))

    async def _failure_checker(self) -> None:
        """Periodically check for agents that have missed heartbeats.

        Emits supervisor:agent-failing events for stale agents.
        """
        from athena_x_runtime_event_bus import BusEvent as BE
        while not self._closed:
            try:
                await asyncio.sleep(self._heartbeat_interval)
                failing = self._registry.list_failing_agents()
                for agent in failing:
                    failing_event = BE.create(
                        event_type="supervisor:agent-failing",
                        provider="health-monitor",
                        agent_id="runtime.health-monitor",
                        payload={
                            "agentId": agent.agent_id,
                            "reason": "missed_heartbeats",
                            "lastSeenAt": agent.last_update.isoformat() if agent.last_update else None,
                        },
                        confidence=0.9,
                    )
                    await self._bus.publish(failing_event)
                    log.warning("agent_failing",
                                agent_id=agent.agent_id,
                                reason="missed_heartbeats")
            except asyncio.CancelledError:
                break
            except Exception as e:
                log.error("failure_checker_error", error=str(e))
