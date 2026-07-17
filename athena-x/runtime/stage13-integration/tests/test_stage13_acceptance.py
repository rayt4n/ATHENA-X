"""Stage 13 acceptance tests - Institutional Operations & Governance Platform."""
import pytest
from athena_x_engine_governance_engine import (
    SystemReadinessScore, SystemStatus,
    ConfidenceArbitrationEngine, SelfHealingEngine, AuditTrail,
    SystemHealthSupervisor,
)
from athena_x_agent_operations_governance import OperationsDNAAgent


@pytest.fixture
def agent():
    return OperationsDNAAgent()


# ============================================================================
# Exit Criteria 1: Every subsystem reports health
# ============================================================================

async def test_subsystem_health_tracked(agent):
    """Subsystems continuously report health."""
    agent.update_subsystem("data_collection", online=True, cpu=45, latency=12)
    agent.update_subsystem("ta_engine", online=True, cpu=30, latency=5)
    dna = await agent.compute_operations_dna()
    assert "data_collection" in dna.system_health
    assert "ta_engine" in dna.system_health


# ============================================================================
# Exit Criteria 2: Agent Health Registry
# ============================================================================

async def test_agent_health_registry(agent):
    """All AI agents are monitored through a registry."""
    agent.update_agent("ta.ema", online=True, success_rate=0.99)
    agent.update_agent("ta.rsi", online=True, success_rate=0.95)
    dna = await agent.compute_operations_dna()
    assert "ta.ema" in dna.agent_health
    assert "ta.rsi" in dna.agent_health


# ============================================================================
# Exit Criteria 3: Confidence Arbitration
# ============================================================================

async def test_confidence_arbitration_resolves_disagreements(agent):
    """Arbitration engine resolves disagreements among 6 DNA objects."""
    agent.set_dna_objects(
        technical="bullish", options="bearish", market="neutral",
        narrative="bullish", forecast="bearish", trade="watch",
    )
    dna = await agent.compute_operations_dna()
    assert dna.confidence_consensus.consensus_direction in ("bullish", "bearish", "neutral")
    assert len(dna.confidence_consensus.conflicts) > 0
    assert dna.confidence_consensus.explanation != ""


# ============================================================================
# Exit Criteria 4: Data integrity + pipeline sync
# ============================================================================

async def test_pipeline_sync_degraded_when_offline(agent):
    """Pipeline sync is degraded when subsystems are offline."""
    agent.update_subsystem("data_collection", online=False)
    dna = await agent.compute_operations_dna()
    assert dna.pipeline_sync == "degraded"


async def test_pipeline_sync_ok_when_all_online(agent):
    """Pipeline sync is synchronized when all subsystems are online."""
    agent.update_subsystem("data_collection", online=True)
    agent.update_subsystem("ta_engine", online=True)
    dna = await agent.compute_operations_dna()
    assert dna.pipeline_sync == "synchronized"


# ============================================================================
# Exit Criteria 5: Plugin governance
# ============================================================================

def test_plugin_governance():
    """Plugin lifecycle is managed."""
    from athena_x_engine_governance_engine import PluginGovernanceEntry
    entry = PluginGovernanceEntry(plugin_id="ema", version="1.0.0", enabled=True, loaded=True)
    assert entry.plugin_id == "ema"
    assert entry.enabled is True


# ============================================================================
# Exit Criteria 6: Model governance
# ============================================================================

def test_model_governance():
    """Forecast model performance is tracked."""
    from athena_x_engine_governance_engine import ModelGovernanceEntry
    entry = ModelGovernanceEntry(model_id="lstm", accuracy=0.65, ensemble_weight=1.2, recommendation="increase_weight")
    assert entry.model_id == "lstm"
    assert entry.recommendation == "increase_weight"


# ============================================================================
# Exit Criteria 7: Self-healing
# ============================================================================

async def test_self_healing_handles_failures(agent):
    """Self-healing attempts automatic recovery."""
    agent.update_subsystem("broken", online=False)
    dna = await agent.compute_operations_dna()
    assert len(dna.self_healing_actions) > 0
    assert all(a.success for a in dna.self_healing_actions)


# ============================================================================
# Exit Criteria 8: Audit trail
# ============================================================================

async def test_audit_trail_records_all_changes(agent):
    """All operational events are recorded in an audit trail."""
    agent.record_audit("config_change", "system", "Enabled plugin: rsi")
    agent.record_audit("model_change", "system", "Updated lstm weight to 1.2")
    dna = await agent.compute_operations_dna()
    assert len(dna.audit_trail) >= 2


# ============================================================================
# Exit Criteria 9: Operations DNA published
# ============================================================================

async def test_operations_dna_published(agent):
    """Operations DNA is published as system:operations_dna event."""
    from athena_x_runtime_event_bus import InMemoryBusClient

    bus = InMemoryBusClient()
    agent._bus = bus

    received = []
    async def handler(event):
        received.append(event)
    await bus.subscribe("system:operations_dna", handler)

    await agent.compute_operations_dna()
    assert len(received) == 1
    await bus.close()


# ============================================================================
# Exit Criteria 10: System Readiness Score
# ============================================================================

async def test_system_readiness_score(agent):
    """System Readiness Score measures platform health."""
    agent.update_subsystem("a", online=True)
    agent.update_subsystem("b", online=True)
    dna = await agent.compute_operations_dna()
    assert 0 <= dna.readiness_score.score <= 100
    assert dna.readiness_score.label in ("Fully Operational", "Operational with Minor Warnings", "Degraded (use caution)", "Major Issues (reports may be unreliable)", "Trading Intelligence Suspended")


async def test_readiness_drops_when_broken(agent):
    """Readiness score drops when subsystems are offline."""
    for i in range(5):
        agent.update_subsystem(f"sub_{i}", online=False)
    dna = await agent.compute_operations_dna()
    assert dna.readiness_score.score < 60
    assert dna.readiness_score.status == SystemStatus.DEGRADED or dna.readiness_score.status == SystemStatus.MAJOR_ISSUES or dna.readiness_score.status == SystemStatus.SUSPENDED


# ============================================================================
# 7th Intelligence Object
# ============================================================================

async def test_7th_intelligence_object(agent):
    """Operations DNA is the 7th intelligence object."""
    dna = await agent.compute_operations_dna()
    d = dna.to_dict()
    assert "overall_status" in d
    assert "readiness_score" in d
    assert "confidence_consensus" in d
    assert "system_risk" in d
    assert "uptime" in d
    assert "pipeline_sync" in d
