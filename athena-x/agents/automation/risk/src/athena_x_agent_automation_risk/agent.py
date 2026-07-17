"""Risk AI — agent implementation."""
from __future__ import annotations


class RiskAgent:
    """
    Risk AI.

    Layer: automation

    Implementation comes in STEP 4 per the order in
    docs/architecture/implementation-order.md.
    """

    agent_id = "automation.risk"
    layer = "automation"

    def __init__(self, config):
        self.config = config
