"""Expected Move AI — agent implementation."""
from __future__ import annotations


class ExpectedMoveAgent:
    """
    Expected Move AI.

    Layer: decision-intelligence

    Implementation comes in STEP 4 per the order in
    docs/architecture/implementation-order.md.
    """

    agent_id = "decision-intelligence.expected-move"
    layer = "decision-intelligence"

    def __init__(self, config):
        self.config = config
