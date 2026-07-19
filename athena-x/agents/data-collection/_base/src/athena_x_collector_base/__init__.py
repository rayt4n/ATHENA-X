"""Base collector framework."""
from .base import BaseCollector, CollectorConfig
from .registry import CollectorRegistry

__all__ = ["BaseCollector", "CollectorConfig", "CollectorRegistry"]
__version__ = "0.1.0"
