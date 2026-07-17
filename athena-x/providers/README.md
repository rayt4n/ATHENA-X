# providers/

Market data provider adapters. Each provider implements the same
`MarketDataProvider` interface, allowing the failover chain to swap
between them transparently.

## Failover chain (Change 1.2 of original STEP 2)

```
Yahoo → Finnhub → Polygon → FlashAlpha → FRED → AlphaVantage
```

If a provider fails, `engines/data-engine/aggregator.py` automatically
fails over to the next. Failover events are published on the bus.

## Provider list

| Provider | Transport | Asset classes |
|---|---|---|
| `yahoo` | REST | equity, etf, index, currency, commodity, yield, volatility, future |
| `finnhub` | WebSocket | equity, etf, currency |
| `polygon` | WebSocket | equity, etf, currency, commodity |
| `flashalpha` | REST | equity, etf, options |
| `fred` | REST | yield, macro indicators |
| `alphavantage` | REST | equity, etf, currency |
| `simulated` | — | all (DEV ONLY — never in production) |

## Interface contract

```python
class MarketDataProvider(Protocol):
    name: str
    async def fetch_quote(self, symbol: str) -> Quote: ...
    async def fetch_bars(self, symbol: str, timeframe: Timeframe, count: int) -> list[Bar]: ...
    async def fetch_option_chain(self, symbol: str, expiry: date) -> OptionChain: ...
    async def health_check(self) -> ProviderHealth: ...
```
