"""Cross-Market Plugin Engine."""
from .manager import CrossMarketPluginManager
from .correlation import CorrelationEngine, CorrelationMatrix
from .leadership import LeadershipEngine, LeadershipResult

__all__ = [
    "CrossMarketPluginManager",
    "CorrelationEngine", "CorrelationMatrix",
    "LeadershipEngine", "LeadershipResult",
]
__version__ = "0.1.0"
