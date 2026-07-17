"""Institutional Operations & Governance Engine."""
from .types import (
    OperationsDNA, SystemReadinessScore, SystemStatus, AgentHealthEntry,
    ConfidenceArbitration, PluginGovernanceEntry,
    ModelGovernanceEntry, AlertEntry, AuditEntry,
    SelfHealingAction, SubsystemHealth,
)
from .health_supervisor import SystemHealthSupervisor
from .confidence_arbitration import ConfidenceArbitrationEngine
from .self_healing import SelfHealingEngine
from .audit_trail import AuditTrail

__all__ = [
    "OperationsDNA", "SystemReadinessScore", "SystemStatus", "AgentHealthEntry",
    "ConfidenceArbitration", "PluginGovernanceEntry",
    "ModelGovernanceEntry", "AlertEntry", "AuditEntry",
    "SelfHealingAction", "SubsystemHealth",
    "SystemHealthSupervisor", "ConfidenceArbitrationEngine",
    "SelfHealingEngine", "AuditTrail",
]
__version__ = "0.1.0"
