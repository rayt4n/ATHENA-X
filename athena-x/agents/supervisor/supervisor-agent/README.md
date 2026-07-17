# Supervisor AI

> Division: **supervisor**
> Team: **core**
> Layer: **supervisor**

Top-level Supervisor. Every division leader reports here. Detects conflicts, checks stale data, detects failing agents, triggers retries, performs confidence weighting, delegates reports, runs self-learning, tracks performance statistics.

## Event subscriptions

- `*`

## Event publications

- `supervisor:conflict-detected`
- `supervisor:agent-failing`
- `supervisor:retry-requested`
- `supervisor:confidence-adjusted`

## Implementation status

- [x] Scaffold (STEP 3.5)
- [ ] Implementation (STEP 4)
- [ ] Tests (STEP 4)
