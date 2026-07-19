"""Governance types - Stage 13.

The 7th intelligence object: Operations DNA.

Answers: "Is the platform healthy enough to trust its intelligence?"
Plus: System Readiness Score (95-100: Fully Operational -> Below 40: Suspended)
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class SystemStatus(str, Enum):
    FULLY_OPERATIONAL = "fully_operational"
    OPERATIONAL_WITH_WARNINGS = "operational_with_warnings"
    DEGRADED = "degraded"
    MAJOR_ISSUES = "major_issues"
    SUSPENDED = "suspended"


@dataclass
class SubsystemHealth:
    """Health of a single subsystem."""
    name: str
    online: bool = True
    cpu: float = 0.0
    memory: float = 0.0
    queue_depth: int = 0
    latency_ms: float = 0.0
    error_rate: float = 0.0
    last_heartbeat: datetime | None = None


@dataclass
class AgentHealthEntry:
    """Health entry for a single AI agent."""
    agent_id: str
    online: bool = True
    version: str = "1.0.0"
    processing_time_ms: float = 0.0
    queue_size: int = 0
    error_count: int = 0
    success_rate: float = 1.0
    last_execution: datetime | None = None
    avg_execution_time_ms: float = 0.0


@dataclass
class ConfidenceArbitration:
    """Resolves disagreements among the 6 intelligence objects."""
    technical_direction: str = "neutral"
    options_direction: str = "neutral"
    market_direction: str = "neutral"
    narrative_direction: str = "neutral"
    forecast_direction: str = "neutral"
    trade_direction: str = "neutral"

    conflicts: list[str] = field(default_factory=list)
    consensus_direction: str = "neutral"
    trust_score: float = 0.5  # 0..1
    explanation: str = ""


@dataclass
class PluginGovernanceEntry:
    """Plugin lifecycle governance."""
    plugin_id: str
    version: str = "1.0.0"
    enabled: bool = True
    loaded: bool = False
    last_reload: datetime | None = None
    test_status: str = "unknown"  # passed, failed, unknown
    failure_count: int = 0


@dataclass
class ModelGovernanceEntry:
    """Forecast model governance."""
    model_id: str
    accuracy: float = 0.5
    mae: float | None = None
    rmse: float | None = None
    calibration: float = 0.5
    regime_performance: dict[str, float] = field(default_factory=dict)
    last_retrained: datetime | None = None
    ensemble_weight: float = 1.0
    recommendation: str = ""  # "increase_weight", "decrease_weight", "retrain", "disable"


@dataclass
class AlertEntry:
    """Institutional alert (no market alerts here)."""
    alert_id: str
    severity: str = "warning"  # critical, warning, info
    category: str = ""  # provider_failure, plugin_crash, etc.
    message: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    resolved: bool = False


@dataclass
class AuditEntry:
    """Immutable audit trail entry."""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    action: str = ""  # config_change, plugin_update, model_change, etc.
    actor: str = ""  # system, user, self_healing
    details: str = ""


@dataclass
class SelfHealingAction:
    """A self-healing action taken by the platform."""
    action_id: str
    action_type: str = ""  # restart_plugin, switch_provider, reload_config, etc.
    target: str = ""
    success: bool = False
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    details: str = ""


@dataclass
class SystemReadinessScore:
    """System Readiness Score (measures the platform, not the market).

    95-100: Fully Operational
    80-94:  Operational with Minor Warnings
    60-79:  Degraded (use caution)
    40-59:  Major Issues (reports may be unreliable)
    Below 40: Trading Intelligence Suspended
    """
    score: int = 100
    label: str = "Fully Operational"
    status: SystemStatus = SystemStatus.FULLY_OPERATIONAL

    def __post_init__(self):
        if self.score >= 95:
            self.label = "Fully Operational"
            self.status = SystemStatus.FULLY_OPERATIONAL
        elif self.score >= 80:
            self.label = "Operational with Minor Warnings"
            self.status = SystemStatus.OPERATIONAL_WITH_WARNINGS
        elif self.score >= 60:
            self.label = "Degraded (use caution)"
            self.status = SystemStatus.DEGRADED
        elif self.score >= 40:
            self.label = "Major Issues (reports may be unreliable)"
            self.status = SystemStatus.MAJOR_ISSUES
        else:
            self.label = "Trading Intelligence Suspended"
            self.status = SystemStatus.SUSPENDED


@dataclass
class OperationsDNA:
    """The 7th intelligence object - Operations DNA.

    Consumed by:
      - Dashboard (Stage 16)
      - Reports (Stage 15)
      - Alert Center
      - Future Auto Trading (V2)
    """
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # System health
    system_health: dict[str, SubsystemHealth] = field(default_factory=dict)
    overall_status: SystemStatus = SystemStatus.FULLY_OPERATIONAL

    # Agent health
    agent_health: dict[str, AgentHealthEntry] = field(default_factory=dict)

    # Confidence arbitration
    confidence_consensus: ConfidenceArbitration = field(default_factory=ConfidenceArbitration)

    # Data integrity
    data_integrity: dict[str, Any] = field(default_factory=dict)
    pipeline_sync: str = "synchronized"  # synchronized, degraded, unsynchronized

    # Plugin governance
    plugin_status: dict[str, PluginGovernanceEntry] = field(default_factory=dict)

    # Model governance
    model_health: dict[str, ModelGovernanceEntry] = field(default_factory=dict)

    # Infrastructure health
    database_health: dict[str, Any] = field(default_factory=dict)
    event_bus_health: dict[str, Any] = field(default_factory=dict)
    provider_health: dict[str, Any] = field(default_factory=dict)

    # Alerts
    alerts: list[AlertEntry] = field(default_factory=list)

    # Self-healing
    self_healing_actions: list[SelfHealingAction] = field(default_factory=list)

    # System risk + readiness
    system_risk: int = 0  # 0 (no risk) to 100 (extreme risk)
    readiness_score: SystemReadinessScore = field(default_factory=SystemReadinessScore)
    uptime: float = 0.0  # seconds
    version: str = "0.1.0"

    # Audit trail (recent)
    audit_trail: list[AuditEntry] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "overall_status": self.overall_status.value,
            "readiness_score": self.readiness_score.score,
            "readiness_label": self.readiness_score.label,
            "system_risk": self.system_risk,
            "uptime": self.uptime,
            "version": self.version,
            "pipeline_sync": self.pipeline_sync,
            "confidence_consensus": {
                "consensus_direction": self.confidence_consensus.consensus_direction,
                "trust_score": self.confidence_consensus.trust_score,
                "conflicts": self.confidence_consensus.conflicts,
                "explanation": self.confidence_consensus.explanation,
            },
            "subsystems_online": sum(1 for s in self.system_health.values() if s.online),
            "subsystems_total": len(self.system_health),
            "agents_online": sum(1 for a in self.agent_health.values() if a.online),
            "agents_total": len(self.agent_health),
            "plugins_enabled": sum(1 for p in self.plugin_status.values() if p.enabled),
            "plugins_total": len(self.plugin_status),
            "active_alerts": len([a for a in self.alerts if not a.resolved]),
            "self_healing_actions": len(self.self_healing_actions),
            "audit_entries": len(self.audit_trail),
        }
