"""Operations DNA Agent - produces the 7th intelligence object.

Stage 13: Governs the platform. Ensures every AI is healthy,
synchronized, trustworthy, and producing reliable intelligence.

Pipeline:
  1. Collect health from all subsystems
  2. Collect health from all AI agents
  3. Arbitrate confidence among 6 DNA objects
  4. Check data integrity + pipeline sync
  5. Check plugin + model governance
  6. Check infrastructure health
  7. Attempt self-healing for failures
  8. Record audit trail
  9. Compute System Readiness Score
  10. Publish Operations DNA
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any
from athena_x_runtime_logger import get_logger
from athena_x_runtime_event_envelope import create_event, EventPriority
from athena_x_engine_governance_engine import (
    OperationsDNA, SystemReadinessScore, SystemStatus,
    SystemHealthSupervisor, ConfidenceArbitrationEngine,
    SelfHealingEngine, AuditTrail,
)

log = get_logger("operations-governance.dna")


class OperationsDNAAgent:
    """Produces Operations DNA from all platform health signals.

    Usage:
        agent = OperationsDNAAgent()
        agent.update_subsystem("data_collection", online=True, cpu=45)
        agent.set_dna_objects(
            technical="bullish", options="bearish", market="neutral",
            narrative="bullish", forecast="bullish", trade="watch",
        )
        dna = await agent.compute_operations_dna()
    """

    def __init__(self, event_bus: Any = None):
        self._bus = event_bus
        self._supervisor = SystemHealthSupervisor()
        self._arbitration = ConfidenceArbitrationEngine()
        self._healing = SelfHealingEngine()
        self._audit = AuditTrail()
        self._dna_objects: dict[str, str] = {}
        self._dna_count = 0
        self._start_time = datetime.now(timezone.utc)

    def update_subsystem(self, name: str, **kwargs) -> None:
        self._supervisor.update_subsystem(name, **kwargs)

    def update_agent(self, agent_id: str, **kwargs) -> None:
        self._supervisor.update_agent(agent_id, **kwargs)

    def set_dna_objects(self, **directions: str) -> None:
        """Set the direction of each DNA object for arbitration."""
        self._dna_objects = directions

    def record_audit(self, action: str, actor: str = "system", details: str = "") -> None:
        self._audit.record(action, actor, details)

    async def compute_operations_dna(self) -> OperationsDNA:
        """Compute the full Operations DNA."""
        dna = OperationsDNA(timestamp=datetime.now(timezone.utc))

        # 1. System health
        dna.system_health = self._supervisor.get_system_health()
        offline_subs = self._supervisor.get_offline_subsystems()

        # 2. Agent health
        dna.agent_health = self._supervisor.get_agent_health()
        offline_agents = self._supervisor.get_offline_agents()

        # 3. Confidence arbitration
        if self._dna_objects:
            dna.confidence_consensus = self._arbitration.arbitrate(
                **self._dna_objects,
                market_regime=self._dna_objects.get("market", "unknown"),
            )

        # 4. Data integrity (simplified)
        dna.data_integrity = {
            "feeds_active": len(dna.system_health),
            "feeds_offline": len(offline_subs),
        }

        # 5. Pipeline sync
        if offline_subs or offline_agents:
            dna.pipeline_sync = "degraded"
        else:
            dna.pipeline_sync = "synchronized"

        # 6. Self-healing for offline components
        for sub in offline_subs:
            action = self._healing.attempt_healing("restart_subsystem", sub)
            dna.self_healing_actions.append(action)
        for agent in offline_agents:
            action = self._healing.attempt_healing("restart_agent", agent)
            dna.self_healing_actions.append(action)

        # 7. Audit trail (recent)
        dna.audit_trail = self._audit.get_entries(limit=20)

        # 8. Compute readiness score
        readiness_score = self._supervisor.compute_readiness_score()
        if offline_subs:
            readiness_score = min(readiness_score, 60)  # cap if subsystems offline
        dna.readiness_score = SystemReadinessScore(score=readiness_score)
        dna.overall_status = dna.readiness_score.status

        # 9. System risk
        dna.system_risk = 100 - readiness_score

        # 10. Uptime
        dna.uptime = (datetime.now(timezone.utc) - self._start_time).total_seconds()

        self._dna_count += 1

        # Publish event
        if self._bus is not None:
            event = create_event(
                event_type="system:operations_dna",
                source_agent="operations-governance.dna",
                symbol="*",
                priority=EventPriority.CRITICAL,
                payload=dna.to_dict(),
            )
            await self._bus.publish(event)

        return dna

    def get_stats(self) -> dict:
        return {
            "operations_dnas_computed": self._dna_count,
            "audit_entries": self._audit.count(),
            "self_healing_stats": self._healing.get_stats(),
        }
