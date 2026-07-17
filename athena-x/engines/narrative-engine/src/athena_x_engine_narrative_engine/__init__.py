"""Narrative Engine."""
from .classifier import EventClassifier
from .impact import MarketImpactEngine
from .timeline import EventTimeline
from .narrative import NarrativeGenerator

__all__ = [
    "EventClassifier", "MarketImpactEngine",
    "EventTimeline", "NarrativeGenerator",
]
__version__ = "0.1.0"
