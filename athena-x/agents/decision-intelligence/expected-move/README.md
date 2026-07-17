# Expected Move AI

> Layer: **decision-intelligence**

Computes expected move (Decision Intelligence layer) — combines options-implied + historical + ATR-based.

## Event subscriptions

- `decision:volatility-projected`
- `options:iv-updated`

## Event publications

- `decision:expected-move-updated`

## Plugin dependencies

- (none)

## Implementation status

- [x] Scaffold
- [ ] Implementation (STEP 4)
- [ ] Tests (STEP 4)
