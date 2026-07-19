"""Simple Moving Average computation plugin."""
from __future__ import annotations


class SmaPlugin:
    """
    Simple Moving Average plugin. Implementation comes in STEP 4.

    The plugin-engine calls `compute(inputs, params)` and expects
    a dict matching the manifest's `outputs` field.
    """

    def compute(self, inputs: dict, params: dict) -> dict:
        raise NotImplementedError("STEP 4 implementation")
