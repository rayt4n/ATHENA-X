# Data Collection Agent

> Layer: **data-collection**

Pulls data from providers (Yahoo → Finnhub → Polygon → FlashAlpha → FRED → AlphaVantage failover chain). Normalizes timestamps. Writes raw payloads to raw_market_data schema.

## Event subscriptions

- (none — source agent)

## Event publications

- `market:quote-updated`
- `market:trade-printed`
- `market:level2-updated`
- `market:bar-closed`
- `market:provider-failed-over`

## Plugin dependencies

- (none)

## Implementation status

- [x] Scaffold
- [ ] Implementation (STEP 4)
- [ ] Tests (STEP 4)
