# Live Dashboard Agent

> Division: **dashboard-reporting**
> Team: **live-dashboard**
> Layer: **7-reporting**

Pushes real-time updates to the frontend via WebSocket. Subscribes to all events the dashboard needs.

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
