"""Macro Agent — agent implementation."""
from __future__ import annotations


class MacroAgentAgent:
    """
    Macro Agent.

    Layer: raw-intelligence

    Implementation comes in STEP 4 per the order in
    docs/architecture/implementation-order.md.
    """

    agent_id = "raw-intelligence.macro-agent"
    layer = "raw-intelligence"

    def __init__(self, config):
        self.config = config
