# Data Validation Agent

> Layer: **data-collection**

Removes duplicates. Detects missing data. Computes data quality scores. Performs cross-provider validation. Rejects low-quality data.

## Event subscriptions

- `market:quote-updated`
- `market:trade-printed`
- `market:bar-closed`

## Event publications

- `system:provider-health-updated`

## Plugin dependencies

- (none)

## Implementation status

- [x] Scaffold
- [ ] Implementation (STEP 4)
- [ ] Tests (STEP 4)
