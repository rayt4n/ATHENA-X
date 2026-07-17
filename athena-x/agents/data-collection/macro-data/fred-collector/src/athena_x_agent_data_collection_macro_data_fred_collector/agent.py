"""FRED Collector — agent implementation."""
from __future__ import annotations


class FredCollectorAgent:
    """
    FRED Collector.

    Division: data-collection
    Layer: 1-provider-adapters

    Implementation comes in STEP 4 per the order in
    docs/architecture/implementation-order.md.
    """

    agent_id = "data-collection.macro-data.fred-collector"
    division = "data-collection"
    layer = "1-provider-adapters"

    def __init__(self, config):
        self.config = config
