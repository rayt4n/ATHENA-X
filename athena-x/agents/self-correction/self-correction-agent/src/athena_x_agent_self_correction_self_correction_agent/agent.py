"""Self-Correction Agent — agent implementation."""
from __future__ import annotations


class SelfCorrectionAgentAgent:
    """
    Self-Correction Agent.

    Layer: self-correction

    Implementation comes in STEP 4 per the order in
    docs/architecture/implementation-order.md.
    """

    agent_id = "self-correction.self-correction-agent"
    layer = "self-correction"

    def __init__(self, config):
        self.config = config
