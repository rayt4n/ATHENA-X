"""0DTE AI — agent implementation."""
from __future__ import annotations


class _0DteAgent:
    """
    0DTE AI.

    Layer: raw-intelligence/options

    Implementation comes in STEP 4 per the order in
    docs/architecture/implementation-order.md.
    """

    agent_id = "raw-intelligence/options.0dte"
    layer = "raw-intelligence/options"

    def __init__(self, config):
        self.config = config
