"""Risk AI — agent implementation."""
from __future__ import annotations


class RiskAgentAgent:
    """
    Risk AI.

    Division: automation
    Layer: future

    Implementation comes in STEP 4 per the order in
    docs/architecture/implementation-order.md.
    """

    agent_id = "automation.risk.risk-agent"
    division = "automation"
    layer = "future"

    def __init__(self, config):
        self.config = config
