"""Symbol dictionary — Stage 4 req 3.

Create one canonical symbol dictionary. Maintain aliases for every provider.

Examples:
  SPY, SPY.US, NYSEARCA:SPY → SPY
  ESU26, ES1!, ES → ES
  BRK-B, BRK.B → BRK.B
"""
from __future__ import annotations
from dataclasses import dataclass, field
from threading import RLock
from typing import Any

from athena_x_runtime_logger import get_logger

log = get_logger("runtime.symbol-dictionary")


@dataclass
class SymbolMapping:
    """A symbol mapping with canonical form + provider aliases."""
    canonical: str
    aliases: dict[str, list[str]] = field(default_factory=dict)  # provider → list of aliases
    asset_class: str = "equity"
    exchange: str | None = None
    description: str = ""

    def add_alias(self, provider: str, alias: str) -> None:
        self.aliases.setdefault(provider, []).append(alias)

    def all_aliases(self) -> list[str]:
        """All aliases across all providers (excluding canonical)."""
        result = []
        for provider_aliases in self.aliases.values():
            result.extend(provider_aliases)
        return result


class SymbolDictionary:
    """Canonical symbol dictionary with provider-specific aliases.

    Usage:
        d = SymbolDictionary()
        d.register("SPY", aliases={"yahoo": ["SPY.US"], "polygon": ["NYSEARCA:SPY"]})
        canonical = d.resolve("SPY.US", provider="yahoo")
        # canonical == "SPY"
    """

    def __init__(self):
        self._mappings: dict[str, SymbolMapping] = {}  # canonical → mapping
        self._alias_index: dict[str, str] = {}  # alias (uppercase) → canonical
        self._lock = RLock()
        self._register_defaults()

    def _register_defaults(self) -> None:
        """Register default mappings for common symbols."""
        # ETFs
        self.register("SPY", aliases={"yahoo": ["SPY.US"], "polygon": ["NYSEARCA:SPY"]},
                       asset_class="etf", exchange="NYSEARCA", description="SPDR S&P 500 ETF")
        self.register("QQQ", aliases={"polygon": ["NASDAQ:QQQ"]},
                       asset_class="etf", exchange="NASDAQ", description="Invesco QQQ Trust")
        self.register("DIA", asset_class="etf", exchange="NYSEARCA", description="SPDR Dow Jones ETF")
        self.register("IWM", asset_class="etf", exchange="NYSEARCA", description="iShares Russell 2000 ETF")
        self.register("SOXX", asset_class="etf", exchange="NASDAQ", description="iShares Semiconductor ETF")

        # Indices
        self.register("SPX", aliases={"yahoo": ["^GSPC"], "polygon": ["I:SPX"]},
                       asset_class="index", description="S&P 500 Index")
        self.register("VIX", aliases={"yahoo": ["^VIX"], "polygon": ["I:VIX"]},
                       asset_class="volatility", description="CBOE Volatility Index")
        self.register("VVIX", aliases={"yahoo": ["^VVIX"]},
                       asset_class="volatility", description="Volatility of Volatility Index")
        self.register("MOVE", asset_class="volatility", description="ICE BofA MOVE Index")
        self.register("DXY", aliases={"yahoo": ["DX-Y.NYB"]},
                       asset_class="currency", description="US Dollar Index")
        self.register("TNX", aliases={"yahoo": ["^TNX"]},
                       asset_class="yield", description="CBOE 10-Year Treasury Yield")

        # Futures
        self.register("ES", aliases={"yahoo": ["ES=F"], "polygon": ["ES1!"], "tradestation": ["ESU26"]},
                       asset_class="future", exchange="CME", description="E-mini S&P 500 Futures")
        self.register("NQ", aliases={"yahoo": ["NQ=F"], "polygon": ["NQ1!"]},
                       asset_class="future", exchange="CME", description="E-mini Nasdaq 100 Futures")

        # Commodities
        self.register("Gold", aliases={"yahoo": ["GC=F", "XAUUSD=X"], "polygon": ["GC1!"]},
                       asset_class="commodity", description="Gold futures")
        self.register("Oil", aliases={"yahoo": ["CL=F"], "polygon": ["CL1!"]},
                       asset_class="commodity", description="WTI Crude Oil futures")
        self.register("Copper", aliases={"yahoo": ["HG=F"]},
                       asset_class="commodity", description="Copper futures")

        # FX
        self.register("USDJPY", aliases={"yahoo": ["JPY=X", "USDJPY=X"]},
                       asset_class="currency", description="USD/JPY exchange rate")

        # Equities (with special symbols)
        self.register("BRK.B", aliases={"yahoo": ["BRK-B"], "polygon": ["BRK.B"]},
                       asset_class="equity", exchange="NYSE", description="Berkshire Hathaway Class B")

        # MAG7
        for sym in ["NVDA", "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA"]:
            self.register(sym, asset_class="equity")

        # Crypto
        self.register("BTC-USD", aliases={"yahoo": ["BTC-USD"], "polygon": ["X:BTCUSD"]},
                       asset_class="crypto", description="Bitcoin")
        self.register("ETH-USD", aliases={"yahoo": ["ETH-USD"], "polygon": ["X:ETHUSD"]},
                       asset_class="crypto", description="Ethereum")

        # Aggregate indices
        self.register("Europe", asset_class="index", description="European equity markets aggregate")
        self.register("Asia", asset_class="index", description="Asian equity markets aggregate")

    def register(
        self,
        canonical: str,
        aliases: dict[str, list[str]] | None = None,
        asset_class: str = "equity",
        exchange: str | None = None,
        description: str = "",
    ) -> None:
        """Register a canonical symbol with provider-specific aliases."""
        with self._lock:
            mapping = SymbolMapping(
                canonical=canonical,
                asset_class=asset_class,
                exchange=exchange,
                description=description,
            )
            if aliases:
                for provider, provider_aliases in aliases.items():
                    for alias in provider_aliases:
                        mapping.add_alias(provider, alias)
                        # Index by uppercase for case-insensitive lookup
                        self._alias_index[alias.upper()] = canonical

            self._mappings[canonical] = mapping
            # Also index canonical itself
            self._alias_index[canonical.upper()] = canonical

    def resolve(self, symbol: str, provider: str | None = None) -> str:
        """Resolve a provider-specific symbol to its canonical form.

        Args:
            symbol: the symbol as returned by the provider
            provider: optional provider name (for provider-specific lookups)

        Returns:
            The canonical symbol (or the original if no mapping found).
        """
        if not symbol:
            return symbol

        with self._lock:
            # Direct lookup (case-insensitive)
            canonical = self._alias_index.get(symbol.upper())
            if canonical:
                return canonical

            # Try provider-specific patterns
            if provider:
                # Strip provider prefixes like "NYSEARCA:", "NASDAQ:", "I:", "X:"
                for prefix in ["NYSEARCA:", "NASDAQ:", "NYSE:", "I:", "X:", "^"]:
                    if symbol.startswith(prefix):
                        stripped = symbol[len(prefix):]
                        canonical = self._alias_index.get(stripped.upper())
                        if canonical:
                            return canonical

            # No mapping found — return original (will be flagged by validator)
            log.warning("symbol_not_in_dictionary", symbol=symbol, provider=provider)
            return symbol

    def get_mapping(self, canonical: str) -> SymbolMapping | None:
        with self._lock:
            return self._mappings.get(canonical)

    def list_all(self) -> list[SymbolMapping]:
        with self._lock:
            return list(self._mappings.values())

    def count(self) -> int:
        with self._lock:
            return len(self._mappings)
