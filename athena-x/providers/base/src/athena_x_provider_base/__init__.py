"""Market data provider base protocol."""
from .types import Quote, Bar, Trade, OptionChain, OptionRow, NewsArticle
from .provider import MarketDataProvider, ProviderResult, ProviderError
from .base_adapter import BaseProviderAdapter

__all__ = [
    "Quote", "Bar", "Trade", "OptionChain", "OptionRow", "NewsArticle",
    "MarketDataProvider", "ProviderResult", "ProviderError",
    "BaseProviderAdapter",
]
__version__ = "0.1.0"
