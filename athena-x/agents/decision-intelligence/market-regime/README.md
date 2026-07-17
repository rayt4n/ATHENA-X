# Market Regime AI

> Layer: **decision-intelligence**

Classifies market regime (Change 9): trending/ranging/breakout/mean-reversion/high-vol/low-vol/news-driven/option-driven/dealer-controlled. No indicator is interpreted without regime context.

## Event subscriptions

- `ta:signal-emitted`
- `options:iv-updated`
- `news:impact-classified`
- `macro:indicator-released`

## Event publications

- `decision:regime-classified`

## Plugin dependencies

- (none)

## Implementation status

- [x] Scaffold
- [ ] Implementation (STEP 4)
- [ ] Tests (STEP 4)
