"""Probability Team Leader — agent implementation."""
from __future__ import annotations


class TeamLeaderAgent:
    """
    Probability Team Leader.

    Division: decision-intelligence
    Layer: 6-decision

    Implementation comes in STEP 4 per the order in
    docs/architecture/implementation-order.md.
    """

    agent_id = "decision-intelligence.probability.team-leader"
    division = "decision-intelligence"
    layer = "6-decision"

    def __init__(self, config):
        self.config = config
