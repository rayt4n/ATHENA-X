"""System Health Supervisor - monitors every subsystem."""
from __future__ import annotations
from datetime import datetime, timezone
from threading import RLock
from typing import Any
from athena_x_engine_governance_engine.types import SubsystemHealth, AgentHealthEntry
from athena_x_runtime_logger import get_logger

log = get_logger("governance.health_supervisor")


class SystemHealthSupervisor:
    """Monitors every subsystem and AI agent.

    Usage:
        supervisor = SystemHealthSupervisor()
        supervisor.update_subsystem("data_collection", online=True, cpu=45, latency=12)
        supervisor.update_agent("ta.ema", online=True, processing_time=5, success_rate=0.99)
        health = supervisor.get_system_health()
    """

    def __init__(self):
        self._subsystems: dict[str, SubsystemHealth] = {}
        self._agents: dict[str, AgentHealthEntry] = {}
        self._lock = RLock()

    def update_subsystem(self, name: str, **kwargs) -> None:
        with self._lock:
            if name not in self._subsystems:
                self._subsystems[name] = SubsystemHealth(name=name)
            sub = self._subsystems[name]
            for k, v in kwargs.items():
                if hasattr(sub, k):
                    setattr(sub, k, v)
            sub.last_heartbeat = datetime.now(timezone.utc)

    def update_agent(self, agent_id: str, **kwargs) -> None:
        with self._lock:
            if agent_id not in self._agents:
                self._agents[agent_id] = AgentHealthEntry(agent_id=agent_id)
            agent = self._agents[agent_id]
            for k, v in kwargs.items():
                if hasattr(agent, k):
                    setattr(agent, k, v)
            agent.last_execution = datetime.now(timezone.utc)

    def get_system_health(self) -> dict[str, SubsystemHealth]:
        with self._lock:
            return dict(self._subsystems)

    def get_agent_health(self) -> dict[str, AgentHealthEntry]:
        with self._lock:
            return dict(self._agents)

    def get_offline_subsystems(self) -> list[str]:
        with self._lock:
            return [name for name, sub in self._subsystems.items() if not sub.online]

    def get_offline_agents(self) -> list[str]:
        with self._lock:
            return [aid for aid, agent in self._agents.items() if not agent.online]

    def compute_readiness_score(self) -> int:
        """Compute system readiness score (0-100)."""
        with self._lock:
            if not self._subsystems:
                return 100
            online_count = sum(1 for s in self._subsystems.values() if s.online)
            total = len(self._subsystems)
            base_score = (online_count / total) * 80

            # Penalize high error rates
            avg_error = sum(s.error_rate for s in self._subsystems.values()) / total if total > 0 else 0
            base_score -= avg_error * 20

            # Penalize high latency
            avg_latency = sum(s.latency_ms for s in self._subsystems.values()) / total if total > 0 else 0
            if avg_latency > 100:
                base_score -= 10

            return max(0, min(100, int(base_score)))
