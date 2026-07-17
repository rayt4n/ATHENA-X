"""Stage 7 acceptance tests - all exit criteria must pass."""
import pytest
from athena_x_runtime_stage7_integration.wire import create_stage7_container
from athena_x_ta_base import Timeframe


@pytest.fixture
def setup():
    return create_stage7_container()


# ============================================================================
# Exit Criteria 1: All 23 TA agents implement the TechnicalIndicator Protocol
# ============================================================================

def test_23_ta_agents_exist(setup):
    """23 TA agents are created (6+8+8+1 = 23, plus supervisor + snapshot = 25)."""
    total = len(setup["layer1"]) + len(setup["layer2"]) + len(setup["layer3"]) + len(setup["layer4"])
    assert total == 23  # 6 + 8 + 8 + 1 = 23


def test_all_agents_have_name_and_layer(setup):
    """Every agent has a name and layer assignment."""
    for agent in setup["all_agents"]:
        assert agent.name is not None
        assert agent.layer in (1, 2, 3, 4, 5)


# ============================================================================
# Exit Criteria 2: Every agent reads from Canonical Repository
# ============================================================================

async def test_agents_read_from_repository(setup, repo):
    """Agents use the repository via bar cache (not direct DB access)."""
    from athena_x_ta_layer2_indicators import EMAAgent
    agent = EMAAgent(bar_cache=setup["bar_cache"])
    result = await agent.compute("SPY", Timeframe.FIFTEEN_MIN, repo)
    assert result.value is not None
    # Bar cache should have been populated (miss -> fetch)
    stats = setup["bar_cache"].get_stats()
    assert stats["misses"] > 0


# ============================================================================
# Exit Criteria 3: No TA agent writes to database
# ============================================================================

def test_no_ta_agent_has_write_methods(setup):
    """TA agents don't have write_quote/write_bar methods."""
    for agent in setup["all_agents"]:
        assert not hasattr(agent, "write_quote")
        assert not hasattr(agent, "write_bar")
        assert not hasattr(agent, "supersede")


# ============================================================================
# Exit Criteria 4: All outputs emitted as ai:technical:* events
# ============================================================================

async def test_outputs_emitted_as_events(setup, repo):
    """TA outputs are published as ai:technical:* events."""
    from athena_x_runtime_event_bus import InMemoryBusClient

    bus = InMemoryBusClient()
    agent = setup["layer2"][0]  # EMAAgent

    received = []
    async def handler(event):
        received.append(event)
    await bus.subscribe("ai:technical:*", handler)

    await agent.compute_and_publish("SPY", Timeframe.FIFTEEN_MIN, repo, event_bus=bus)

    assert len(received) == 1
    assert received[0].event_type.startswith("ai:technical:")
    await bus.close()


# ============================================================================
# Exit Criteria 5: Multi-timeframe synchronization working
# ============================================================================

async def test_multi_timeframe_synchronization(setup, repo):
    """Multi-Timeframe Data Agent fetches across all 8 timeframes."""
    agent = setup["layer1"][5]  # MultiTimeframeDataAgent
    result = await agent.compute("SPY", Timeframe.DAILY, repo)
    assert len(result.value) == 9  # 9 timeframes


# ============================================================================
# Exit Criteria 6: Timeframe Consensus Agent publishes unified view
# ============================================================================

async def test_consensus_publishes_unified_view(setup, repo):
    """Consensus agent produces a unified market view."""
    agent = setup["layer4"][0]  # TimeframeConsensusAgent
    result = await agent.compute("SPY", Timeframe.DAILY, repo)
    assert "alignment" in result.value
    assert "long_term" in result.value
    assert "intraday" in result.value


# ============================================================================
# Exit Criteria 7: Interpretive agents consume lower-layer outputs
# ============================================================================

async def test_layer3_consumes_lower_layers(setup, repo):
    """Layer 3 agents metadata shows they consume layers 1+2."""
    for agent in setup["layer3"]:
        result = await agent.compute("SPY", Timeframe.FIFTEEN_MIN, repo)
        assert result.metadata.get("consumes_layers") == [1, 2]


# ============================================================================
# Exit Criteria 8: Technical Supervisor monitors all agents
# ============================================================================

async def test_supervisor_monitors_all_agents(setup, repo):
    """Supervisor monitors all registered agents."""
    sup = setup["supervisor"]
    result = await sup.compute("SPY", Timeframe.DAILY, repo)
    assert result.value["total_agents"] == 23  # 6+8+8+1


# ============================================================================
# Exit Criteria 9: Shared bar caching eliminates redundant reads
# ============================================================================

async def test_bar_cache_eliminates_redundant_reads(setup, repo):
    """Multiple indicators using the same bars benefit from cache."""
    cache = setup["bar_cache"]

    # Run EMA (first call -> miss)
    ema = setup["layer2"][0]
    await ema.compute("SPY", Timeframe.FIFTEEN_MIN, repo)

    # Run RSI (same bars -> should hit cache)
    rsi = setup["layer2"][3]
    await rsi.compute("SPY", Timeframe.FIFTEEN_MIN, repo)

    stats = cache.get_stats()
    assert stats["hits"] > 0  # at least 1 cache hit


# ============================================================================
# Exit Criteria 10: Technical Snapshot for downstream consumption
# ============================================================================

async def test_technical_snapshot_provides_single_view(setup, repo):
    """Snapshot agent produces a single synchronized view for downstream."""
    agent = setup["snapshot"]
    result = await agent.compute("SPY", Timeframe.FIFTEEN_MIN, repo)

    # Contains data from all layers
    value = result.value
    assert "trend" in value       # Layer 1
    assert "ema" in value         # Layer 2
    assert "wyckoff_phase" in value  # Layer 3
    assert "alignment_score" in value  # Layer 4
    assert "overall_confidence" in value


# ============================================================================
# Stress test: run all 23 agents
# ============================================================================

async def test_stress_all_23_agents_run(setup, repo):
    """All 23 agents can run without errors."""
    all_ta = setup["layer1"] + setup["layer2"] + setup["layer3"] + setup["layer4"]
    for agent in all_ta:
        result = await agent.compute("SPY", Timeframe.FIFTEEN_MIN, repo)
        assert result is not None


# ============================================================================
# Confidence score on every output
# ============================================================================

async def test_every_output_has_confidence(setup, repo):
    """Every TA output includes confidence metadata."""
    all_ta = setup["layer1"] + setup["layer2"] + setup["layer3"] + setup["layer4"]
    for agent in all_ta:
        result = await agent.compute("SPY", Timeframe.FIFTEEN_MIN, repo)
        assert result.confidence is not None
        assert 0 <= result.confidence.score <= 1.0
        assert result.confidence.quality in ("A+", "A", "B", "C", "D", "F")
