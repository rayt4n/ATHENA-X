"""FX AI — agent implementation."""
from __future__ import annotations


class FxAgentAgent:
    """
    FX AI.

    Division: macro-intelligence
    Layer: 5-intelligence

    Implementation comes in STEP 4 per the order in
    docs/architecture/implementation-order.md.
    """

    agent_id = "macro-intelligence.fx.fx-agent"
    division = "macro-intelligence"
    layer = "5-intelligence"

    def __init__(self, config):
        self.config = config
