"""Supervisor AI — agent implementation."""
from __future__ import annotations


class SupervisorAgentAgent:
    """
    Supervisor AI.

    Layer: supervisor

    Implementation comes in STEP 4 per the order in
    docs/architecture/implementation-order.md.
    """

    agent_id = "supervisor.supervisor-agent"
    layer = "supervisor"

    def __init__(self, config):
        self.config = config
