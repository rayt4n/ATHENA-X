# IV AI

> Division: **options-intelligence**
> Team: **iv**
> Layer: **5-intelligence**

Computes implied volatility via Brent's method.

## Event subscriptions

- `market:bar-closed`

## Event publications

- `options:iv-updated`
- `options:greeks-computed`
- `options:chain-refreshed`
- `options:gamma-exposure-updated`
- `options:max-pain-updated`
- `options:unusual-activity`

## Implementation status

- [x] Scaffold (STEP 3.5)
- [ ] Implementation (STEP 4)
- [ ] Tests (STEP 4)
