"""Oil Team Leader — agent implementation."""
from __future__ import annotations


class TeamLeaderAgent:
    """
    Oil Team Leader.

    Division: macro-intelligence
    Layer: 5-intelligence

    Implementation comes in STEP 4 per the order in
    docs/architecture/implementation-order.md.
    """

    agent_id = "macro-intelligence.oil.team-leader"
    division = "macro-intelligence"
    layer = "5-intelligence"

    def __init__(self, config):
        self.config = config
