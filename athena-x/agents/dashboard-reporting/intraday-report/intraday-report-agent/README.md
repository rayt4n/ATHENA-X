# Intraday Report Agent

> Division: **dashboard-reporting**
> Team: **intraday-report**
> Layer: **7-reporting**

Generates intraday snapshots every 15 minutes during market hours.

## Event subscriptions

- (source agent — no subscriptions)

## Event publications

- `report:generation-started`
- `report:generation-completed`
- `report:exported`
- `report:stored`

## Implementation status

- [x] Scaffold (STEP 3.5)
- [ ] Implementation (STEP 4)
- [ ] Tests (STEP 4)
