# Price Validator Agent

> Division: **validation**
> Team: **price-validator**
> Layer: **2-validation**

Cross-source price validation. If Yahoo says 752.44, Polygon 752.46, Finnhub 752.45 → tolerance < 0.02 → Verified. If one says 742 → REJECT.

## Event subscriptions

- (source agent — no subscriptions)

## Event publications

- (sink agent — no publications)

## Implementation status

- [x] Scaffold (STEP 3.5)
- [ ] Implementation (STEP 4)
- [ ] Tests (STEP 4)
