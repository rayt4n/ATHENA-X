"""Alternative Data Team Leader — agent implementation."""
from __future__ import annotations


class TeamLeaderAgent:
    """
    Alternative Data Team Leader.

    Division: data-collection
    Layer: 1-provider-adapters

    Implementation comes in STEP 4 per the order in
    docs/architecture/implementation-order.md.
    """

    agent_id = "data-collection.alternative-data.team-leader"
    division = "data-collection"
    layer = "1-provider-adapters"

    def __init__(self, config):
        self.config = config
