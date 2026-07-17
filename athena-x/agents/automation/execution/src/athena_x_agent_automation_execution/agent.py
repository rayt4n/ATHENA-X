"""Execution AI — agent implementation."""
from __future__ import annotations


class ExecutionAgent:
    """
    Execution AI.

    Layer: automation

    Implementation comes in STEP 4 per the order in
    docs/architecture/implementation-order.md.
    """

    agent_id = "automation.execution"
    layer = "automation"

    def __init__(self, config):
        self.config = config
