"""Tests for Governance Engine."""
import pytest
from athena_x_engine_governance_engine import (
    OperationsDNA, SystemReadinessScore, AgentHealthEntry,
    ConfidenceArbitration, PluginGovernanceEntry,
    ModelGovernanceEntry, AlertEntry, AuditEntry,
    SelfHealingAction, SubsystemHealth,
    SystemHealthSupervisor, ConfidenceArbitrationEngine,
    SelfHealingEngine, AuditTrail,
)


# ============================================================================
# System Health Supervisor tests
# ============================================================================

def test_supervisor_tracks_subsystems():
    sup = SystemHealthSupervisor()
    sup.update_subsystem("data_collection", online=True, cpu=45, latency=12)
    health = sup.get_system_health()
    assert "data_collection" in health
    assert health["data_collection"].online is True


def test_supervisor_tracks_agents():
    sup = SystemHealthSupervisor()
    sup.update_agent("ta.ema", online=True, processing_time=5, success_rate=0.99)
    agents = sup.get_agent_health()
    assert "ta.ema" in agents
    assert agents["ta.ema"].success_rate == 0.99


def test_supervisor_readiness_score():
    sup = SystemHealthSupervisor()
    sup.update_subsystem("a", online=True)
    sup.update_subsystem("b", online=True)
    sup.update_subsystem("c", online=False)
    score = sup.compute_readiness_score()
    assert 40 <= score <= 80  # 2/3 online -> ~53


# ============================================================================
# Confidence Arbitration tests
# ============================================================================

def test_arbitration_no_conflict():
    engine = ConfidenceArbitrationEngine()
    result = engine.arbitrate(
        technical="bullish", options="bullish", market="bullish",
        narrative="bullish", forecast="bullish", trade="bullish",
    )
    assert result.consensus_direction == "bullish"
    assert len(result.conflicts) == 0
    assert result.trust_score > 0.8


def test_arbitration_detects_conflict():
    engine = ConfidenceArbitrationEngine()
    result = engine.arbitrate(
        technical="bullish", options="bearish", market="neutral",
        narrative="bullish", forecast="bearish", trade="watch",
    )
    assert len(result.conflicts) > 0
    assert "Technical" in result.conflicts[0] or "bullish" in result.conflicts[0].lower()


def test_arbitration_weights_by_regime():
    """Risk-On regime weights technical + forecast higher."""
    engine = ConfidenceArbitrationEngine()
    result = engine.arbitrate(
        technical="bullish", options="bearish",
        market="Risk-On", narrative="neutral", forecast="bullish", trade="neutral",
        market_regime="Risk-On",
    )
    # Technical + forecast weighted higher in Risk-On -> bullish
    assert result.consensus_direction == "bullish"


def test_arbitration_trust_score():
    """Trust score is higher when objects agree."""
    engine = ConfidenceArbitrationEngine()
    agree = engine.arbitrate(technical="bullish", options="bullish", forecast="bullish")
    disagree = engine.arbitrate(technical="bullish", options="bearish", forecast="bullish")
    assert agree.trust_score > disagree.trust_score


# ============================================================================
# Self-Healing tests
# ============================================================================

def test_self_healing_attempts_recovery():
    engine = SelfHealingEngine()
    action = engine.attempt_healing("restart_plugin", "ta.ema")
    assert action.action_type == "restart_plugin"
    assert action.target == "ta.ema"
    assert action.success is True


def test_self_healing_stats():
    engine = SelfHealingEngine()
    engine.attempt_healing("restart_plugin", "a")
    engine.attempt_healing("switch_provider", "b")
    stats = engine.get_stats()
    assert stats["total_actions"] == 2
    assert stats["success_rate"] == 1.0


# ============================================================================
# Audit Trail tests
# ============================================================================

def test_audit_trail_records():
    trail = AuditTrail()
    trail.record("config_change", "system", "Enabled plugin: rsi")
    trail.record("plugin_update", "system", "Updated: lstm to v2.0")
    assert trail.count() == 2


def test_audit_trail_filter():
    trail = AuditTrail()
    trail.record("config_change", "system", "change 1")
    trail.record("plugin_update", "system", "update 1")
    trail.record("config_change", "system", "change 2")
    filtered = trail.get_entries(action_filter="config_change")
    assert len(filtered) == 2


# ============================================================================
# System Readiness Score tests
# ============================================================================

def test_readiness_score_fully_operational():
    score = SystemReadinessScore(score=97)
    assert score.label == "Fully Operational"


def test_readiness_score_minor_warnings():
    score = SystemReadinessScore(score=85)
    assert score.label == "Operational with Minor Warnings"


def test_readiness_score_degraded():
    score = SystemReadinessScore(score=65)
    assert score.label == "Degraded (use caution)"


def test_readiness_score_major_issues():
    score = SystemReadinessScore(score=45)
    assert score.label == "Major Issues (reports may be unreliable)"


def test_readiness_score_suspended():
    score = SystemReadinessScore(score=30)
    assert score.label == "Trading Intelligence Suspended"


# ============================================================================
# Operations DNA tests
# ============================================================================

def test_operations_dna_has_all_fields():
    dna = OperationsDNA()
    assert dna.overall_status is not None
    assert dna.confidence_consensus is not None
    assert dna.readiness_score is not None
    assert dna.alerts == []
    assert dna.audit_trail == []


def test_operations_dna_serializable():
    dna = OperationsDNA()
    d = dna.to_dict()
    assert "overall_status" in d
    assert "readiness_score" in d
    assert "confidence_consensus" in d
