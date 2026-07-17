"""Data Collection Agent — agent implementation."""
from __future__ import annotations


class CollectionAgentAgent:
    """
    Data Collection Agent.

    Layer: data-collection

    Implementation comes in STEP 4 per the order in
    docs/architecture/implementation-order.md.
    """

    agent_id = "data-collection.collection-agent"
    layer = "data-collection"

    def __init__(self, config):
        self.config = config
