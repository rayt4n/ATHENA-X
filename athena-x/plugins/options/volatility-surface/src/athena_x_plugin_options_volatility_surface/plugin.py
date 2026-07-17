"""Volatility Surface Builder computation plugin."""
from __future__ import annotations


class VolatilitySurfacePlugin:
    """Implementation comes in STEP 4."""

    def compute(self, inputs: dict, params: dict) -> dict:
        raise NotImplementedError("STEP 4 implementation")
