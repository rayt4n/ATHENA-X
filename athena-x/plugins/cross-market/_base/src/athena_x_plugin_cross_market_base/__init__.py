"""CrossMarketPlugin Protocol - stable interface for all cross-market plugins."""
from .protocol import (
    CrossMarketPlugin, MarketDataInput, CrossMarketOutput,
    CrossMarketCategory, MarketGroup,
)

__all__ = [
    "CrossMarketPlugin", "MarketDataInput", "CrossMarketOutput",
    "CrossMarketCategory", "MarketGroup",
]
__version__ = "0.1.0"
