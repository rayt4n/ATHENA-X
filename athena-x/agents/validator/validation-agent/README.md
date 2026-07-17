# Institutional Validation Agent

> Layer: **validator**

Institutional Validation Layer (Change 4). Before any report reaches the dashboard: confidence ≥ threshold, evidence ≥ minimum, data freshness within window, source count ≥ minimum, agreement score ≥ threshold. Publishes report-approved or report-rejected.

## Event subscriptions

- `report:generation-completed`

## Event publications

- `validator:report-approved`
- `validator:report-rejected`
- `validator:backtest-run`
- `validator:calibration-updated`

## Plugin dependencies

- (none)

## Implementation status

- [x] Scaffold
- [ ] Implementation (STEP 4)
- [ ] Tests (STEP 4)
