"""Broker API Adapter — agent implementation."""
from __future__ import annotations


class BrokerAgentAgent:
    """
    Broker API Adapter.

    Division: automation
    Layer: future

    Implementation comes in STEP 4 per the order in
    docs/architecture/implementation-order.md.
    """

    agent_id = "automation.broker.broker-agent"
    division = "automation"
    layer = "future"

    def __init__(self, config):
        self.config = config
