"""Broker API Adapter — agent implementation."""
from __future__ import annotations


class BrokerAgent:
    """
    Broker API Adapter.

    Layer: automation

    Implementation comes in STEP 4 per the order in
    docs/architecture/implementation-order.md.
    """

    agent_id = "automation.broker"
    layer = "automation"

    def __init__(self, config):
        self.config = config
