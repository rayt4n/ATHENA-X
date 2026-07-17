"""News Agent — agent implementation."""
from __future__ import annotations


class NewsAgentAgent:
    """
    News Agent.

    Layer: raw-intelligence

    Implementation comes in STEP 4 per the order in
    docs/architecture/implementation-order.md.
    """

    agent_id = "raw-intelligence.news-agent"
    layer = "raw-intelligence"

    def __init__(self, config):
        self.config = config
