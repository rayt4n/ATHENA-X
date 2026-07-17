"""CNBC Collector — agent implementation."""
from __future__ import annotations


class CnbcCollectorAgent:
    """
    CNBC Collector.

    Division: data-collection
    Layer: 1-provider-adapters

    Implementation comes in STEP 4 per the order in
    docs/architecture/implementation-order.md.
    """

    agent_id = "data-collection.news-data.cnbc-collector"
    division = "data-collection"
    layer = "1-provider-adapters"

    def __init__(self, config):
        self.config = config
