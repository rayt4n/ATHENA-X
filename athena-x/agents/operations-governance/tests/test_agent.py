"""Tests for Operations DNA Agent."""
import pytest
from athena_x_agent_operations_governance import OperationsDNAAgent
from athena_x_engine_governance_engine import SystemStatus


@pytest.fixture
def agent():
    return OperationsDNAAgent()


async def test_operations_dna_produced(agent):
    """Operations DNA Agent produces OperationsDNA."""
    dna = await agent.compute_operations_dna()
    assert dna.timestamp is not None
    assert dna.overall_status is not None
    assert dna.readiness_score is not None


async def test_operations_dna_includes_readiness(agent):
    """Operations DNA includes System Readiness Score."""
    agent.update_subsystem("data_collection", online=True)
    agent.update_subsystem("ta_engine", online=True)
    dna = await agent.compute_operations_dna()
    assert 0 <= dna.readiness_score.score <= 100
    assert dna.readiness_score.label in ("Fully Operational", "Operational with Minor Warnings", "Degraded (use caution)", "Major Issues (reports may be unreliable)", "Trading Intelligence Suspended")


async def test_operations_dna_includes_confidence_arbitration(agent):
    """Operations DNA includes confidence arbitration."""
    agent.set_dna_objects(
        technical="bullish", options="bullish", market="bullish",
        narrative="bullish", forecast="bullish", trade="bullish",
    )
    dna = await agent.compute_operations_dna()
    assert dna.confidence_consensus.consensus_direction == "bullish"
    assert dna.confidence_consensus.trust_score > 0.7


async def test_operations_dna_detects_conflicts(agent):
    """Operations DNA detects conflicts between DNA objects."""
    agent.set_dna_objects(
        technical="bullish", options="bearish", market="neutral",
        narrative="bullish", forecast="bearish", trade="watch",
    )
    dna = await agent.compute_operations_dna()
    assert len(dna.confidence_consensus.conflicts) > 0


async def test_operations_dna_includes_audit_trail(agent):
    """Operations DNA includes recent audit trail."""
    agent.record_audit("config_change", "system", "Enabled plugin: rsi")
    dna = await agent.compute_operations_dna()
    assert len(dna.audit_trail) > 0


async def test_operations_dna_includes_self_healing(agent):
    """Operations DNA includes self-healing actions for offline components."""
    agent.update_subsystem("broken_subsystem", online=False)
    dna = await agent.compute_operations_dna()
    assert len(dna.self_healing_actions) > 0


async def test_operations_dna_event_published(agent):
    """Operations DNA publishes system:operations_dna event."""
    from athena_x_runtime_event_bus import InMemoryBusClient

    bus = InMemoryBusClient()
    agent._bus = bus

    received = []
    async def handler(event):
        received.append(event)
    await bus.subscribe("system:operations_dna", handler)

    await agent.compute_operations_dna()
    assert len(received) == 1
    assert "readiness_score" in received[0].payload
    await bus.close()


async def test_operations_dna_suspended_when_broken(agent):
    """Readiness score drops when subsystems are offline."""
    # All subsystems offline
    for i in range(5):
        agent.update_subsystem(f"sub_{i}", online=False)

    dna = await agent.compute_operations_dna()
    assert dna.readiness_score.score < 60


async def test_7th_intelligence_object(agent):
    """Operations DNA is the 7th intelligence object."""
    dna = await agent.compute_operations_dna()
    d = dna.to_dict()
    assert "overall_status" in d
    assert "readiness_score" in d
    assert "confidence_consensus" in d
    assert "system_risk" in d
    assert "uptime" in d
