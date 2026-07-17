"""Probability Engine — agent implementation."""
from __future__ import annotations


class ProbabilityEngineAgent:
    """
    Probability Engine.

    Layer: decision-intelligence

    Implementation comes in STEP 4 per the order in
    docs/architecture/implementation-order.md.
    """

    agent_id = "decision-intelligence.probability-engine"
    layer = "decision-intelligence"

    def __init__(self, config):
        self.config = config
