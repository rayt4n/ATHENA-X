"""Technical Supervisor - Layer 5.

Stage 7 req: One supervisor monitors all TA agents.

Responsibilities:
  - Detect failed calculations
  - Detect stale indicators
  - Detect inconsistent timeframes
  - Restart failed agents
  - Measure latency
  - Measure calculation duration
  - Publish health events
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any

from athena_x_ta_base import BaseTAAgent, TAOutput, TAConfidence, Timeframe


@dataclass
class SupervisorReport:
    """Report from the Technical Supervisor."""
    total_agents: int = 0
    active_agents: int = 0
    failed_agents: list[str] = field(default_factory=list)
    stale_agents: list[str] = field(default_factory=list)
    avg_latency_ms: float = 0.0
    max_latency_ms: float = 0.0
    timeframe_sync_status: str = "synced"  # synced / desynchronized
    health_events: list[dict] = field(default_factory=list)


class TechnicalSupervisor(BaseTAAgent):
    """Monitors all TA agents.

    Stage 7 rule: Publishes health events for the overall Supervisor AI.
    """

    def __init__(self, stale_threshold_seconds: float = 60.0, **kwargs):
        super().__init__(name="technical_supervisor", layer=5, **kwargs)
        self._stale_threshold = stale_threshold_seconds
        self._registered_agents: list[BaseTAAgent] = []

    def register_agent(self, agent: BaseTAAgent) -> None:
        """Register a TA agent for monitoring."""
        self._registered_agents.append(agent)

    async def compute(self, symbol: str, timeframe: Timeframe, repo) -> TAOutput:
        """Compute supervisor report."""
        now = datetime.now(timezone.utc)
        report = SupervisorReport(total_agents=len(self._registered_agents))

        latencies = []
        for agent in self._registered_agents:
            health = agent.get_health()
            if not health["running"]:
                report.failed_agents.append(agent.name)
            elif health["last_calculation"]:
                last = datetime.fromisoformat(health["last_calculation"])
                age = (now - last).total_seconds()
                if age > self._stale_threshold:
                    report.stale_agents.append(agent.name)
                else:
                    report.active_agents += 1
            latencies.append(health.get("avg_calculation_time_ms", 0))

        if latencies:
            report.avg_latency_ms = sum(latencies) / len(latencies)
            report.max_latency_ms = max(latencies)

        # Check timeframe synchronization
        if report.stale_agents:
            report.timeframe_sync_status = "desynchronized"

        # Build health events
        if report.failed_agents:
            report.health_events.append({
                "type": "agents_failed",
                "agents": report.failed_agents,
                "severity": "critical",
            })
        if report.stale_agents:
            report.health_events.append({
                "type": "agents_stale",
                "agents": report.stale_agents,
                "severity": "warning",
            })

        return TAOutput(
            agent=self.name, symbol=symbol, timeframe="ALL",
            indicator="TechnicalSupervisor",
            value={
                "total_agents": report.total_agents,
                "active_agents": report.active_agents,
                "failed_agents": report.failed_agents,
                "stale_agents": report.stale_agents,
                "avg_latency_ms": round(report.avg_latency_ms, 2),
                "max_latency_ms": round(report.max_latency_ms, 2),
                "timeframe_sync": report.timeframe_sync_status,
                "health_events": report.health_events,
            },
            confidence=TAConfidence.from_score(0.95),
            metadata={"registered": len(self._registered_agents)},
        )
