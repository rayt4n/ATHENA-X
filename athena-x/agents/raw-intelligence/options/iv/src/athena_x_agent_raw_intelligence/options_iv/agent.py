"""IV AI — agent implementation."""
from __future__ import annotations


class IvAgent:
    """
    IV AI.

    Layer: raw-intelligence/options

    Implementation comes in STEP 4 per the order in
    docs/architecture/implementation-order.md.
    """

    agent_id = "raw-intelligence/options.iv"
    layer = "raw-intelligence/options"

    def __init__(self, config):
        self.config = config
