# Greeks AI

> Division: **options-intelligence**
> Team: **greeks**
> Layer: **5-intelligence**

Computes option Greeks (delta, gamma, theta, vega, rho).

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
