"""Probability Tree AI — agent implementation."""
from __future__ import annotations


class ProbabilityTreeAgent:
    """
    Probability Tree AI.

    Layer: decision-intelligence

    Implementation comes in STEP 4 per the order in
    docs/architecture/implementation-order.md.
    """

    agent_id = "decision-intelligence.probability-tree"
    layer = "decision-intelligence"

    def __init__(self, config):
        self.config = config
