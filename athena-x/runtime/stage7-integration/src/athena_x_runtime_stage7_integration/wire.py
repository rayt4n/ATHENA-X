"""Wire Stage 7 TA engine with all 5 layers + snapshot + supervisor."""
from __future__ import annotations
from athena_x_ta_base import BarCache, TimeframeContext
from athena_x_ta_layer1_market_structure import (
    TrendDetectionAgent, SwingHighLowAgent, SupportResistanceAgent,
    LiquidityAgent, VolumeProfileAgent, MultiTimeframeDataAgent,
)
from athena_x_ta_layer2_indicators import (
    EMAAgent, SMAAgent, VWAPAgent, RSIAgent,
    MACDAgent, ADXAgent, ATRAgent, BollingerAgent,
)
from athena_x_ta_layer3_institutional import (
    WyckoffAgent, ChanTheoryAgent, ElliottWaveAgent,
    SmartMoneyAgent, VolumePriceAgent,
    EscapeTopAgent, EntryAgent, PullUpPatternAgent,
)
from athena_x_ta_layer4_consensus import TimeframeConsensusAgent
from athena_x_ta_layer5_supervisor import TechnicalSupervisor
from athena_x_ta_snapshot import TechnicalSnapshotAgent


def create_stage7_container():
    """Create full TA engine wiring."""
    bar_cache = BarCache()
    tf_ctx = TimeframeContext()

    # Layer 1: 6 agents
    layer1 = [
        TrendDetectionAgent(bar_cache=bar_cache),
        SwingHighLowAgent(bar_cache=bar_cache),
        SupportResistanceAgent(bar_cache=bar_cache),
        LiquidityAgent(bar_cache=bar_cache),
        VolumeProfileAgent(bar_cache=bar_cache),
        MultiTimeframeDataAgent(bar_cache=bar_cache),
    ]

    # Layer 2: 8 agents
    layer2 = [
        EMAAgent(bar_cache=bar_cache),
        SMAAgent(bar_cache=bar_cache),
        VWAPAgent(bar_cache=bar_cache),
        RSIAgent(bar_cache=bar_cache),
        MACDAgent(bar_cache=bar_cache),
        ADXAgent(bar_cache=bar_cache),
        ATRAgent(bar_cache=bar_cache),
        BollingerAgent(bar_cache=bar_cache),
    ]

    # Layer 3: 8 agents
    layer3 = [
        WyckoffAgent(bar_cache=bar_cache),
        ChanTheoryAgent(bar_cache=bar_cache),
        ElliottWaveAgent(bar_cache=bar_cache),
        SmartMoneyAgent(bar_cache=bar_cache),
        VolumePriceAgent(bar_cache=bar_cache),
        EscapeTopAgent(bar_cache=bar_cache),
        EntryAgent(bar_cache=bar_cache),
        PullUpPatternAgent(bar_cache=bar_cache),
    ]

    # Layer 4: 1 agent
    layer4 = [TimeframeConsensusAgent(bar_cache=bar_cache)]

    # Layer 5: 1 supervisor
    supervisor = TechnicalSupervisor(bar_cache=bar_cache)
    for agent in layer1 + layer2 + layer3 + layer4:
        supervisor.register_agent(agent)

    # Snapshot agent
    snapshot = TechnicalSnapshotAgent(bar_cache=bar_cache)

    all_agents = layer1 + layer2 + layer3 + layer4 + [supervisor, snapshot]

    return {
        "bar_cache": bar_cache,
        "timeframe_context": tf_ctx,
        "layer1": layer1,
        "layer2": layer2,
        "layer3": layer3,
        "layer4": layer4,
        "supervisor": supervisor,
        "snapshot": snapshot,
        "all_agents": all_agents,
        "total_agent_count": len(all_agents),
    }
