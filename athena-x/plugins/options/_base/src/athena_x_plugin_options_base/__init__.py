"""OptionsPlugin Protocol - stable interface for all options intelligence plugins.

Stage 8: Every options metric is an independent plugin.
The engine doesn't know which metrics exist. It only loads plugins.

OptionsPlugin (Protocol)
|_ IV
|_ IVRank
|_ GammaExposure
|_ GammaFlip
|_ MaxPain
|_ OptionFlow
|_ DealerPosition
|_ DarkPool
|_ 0DTE Positioning
|_ ... (40+ plugins)
|_ FutureMetric  <- can be added without changing consumers
"""
from .protocol import (
    OptionsPlugin, OptionsPluginInput, OptionsPluginOutput,
    OptionsPluginCategory, OptionsPluginConfig,
)

__all__ = [
    "OptionsPlugin", "OptionsPluginInput", "OptionsPluginOutput",
    "OptionsPluginCategory", "OptionsPluginConfig",
]
__version__ = "0.1.0"
