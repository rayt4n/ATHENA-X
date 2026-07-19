"""Moving Average Convergence Divergence computation plugin."""
from __future__ import annotations


class MacdPlugin:
    """
    Moving Average Convergence Divergence plugin. Implementation comes in STEP 4.

    The plugin-engine calls `compute(inputs, params)` and expects
    a dict matching the manifest's `outputs` field.
    """

    def compute(self, inputs: dict, params: dict) -> dict:
        raise NotImplementedError("STEP 4 implementation")
