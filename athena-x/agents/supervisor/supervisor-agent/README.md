# Supervisor AI

> Layer: **supervisor**

Every AI agent reports to the Supervisor (Change 3). Detects conflicting signals, checks stale data, detects failing agents, triggers retries, performs confidence weighting, delegates report generation, runs self-learning, and tracks performance statistics.

## Event subscriptions

- `*`

## Event publications

- `supervisor:conflict-detected`
- `supervisor:agent-failing`
- `supervisor:retry-requested`
- `supervisor:confidence-adjusted`

## Plugin dependencies

- (none)

## Implementation status

- [x] Scaffold
- [ ] Implementation (STEP 4)
- [ ] Tests (STEP 4)
