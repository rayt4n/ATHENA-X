"""IV AI — agent implementation."""
from __future__ import annotations


class IvAgentAgent:
    """
    IV AI.

    Division: options-intelligence
    Layer: 5-intelligence

    Implementation comes in STEP 4 per the order in
    docs/architecture/implementation-order.md.
    """

    agent_id = "options-intelligence.iv.iv-agent"
    division = "options-intelligence"
    layer = "5-intelligence"

    def __init__(self, config):
        self.config = config
