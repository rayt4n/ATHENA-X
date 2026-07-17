"""DIA Cross-Market Agent — agent implementation."""
from __future__ import annotations


class DiaAgent:
    """
    DIA Cross-Market Agent.

    Layer: raw-intelligence/cross-market

    Implementation comes in STEP 4 per the order in
    docs/architecture/implementation-order.md.
    """

    agent_id = "raw-intelligence/cross-market.dia"
    layer = "raw-intelligence/cross-market"

    def __init__(self, config):
        self.config = config
