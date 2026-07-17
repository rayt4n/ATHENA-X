# Self-Correction Agent

> Layer: **self-correction**

Continuous learning engine (Change 12). Pipeline: prediction → market outcome → compare → error → weight adjustment → improve model. Every prediction is scored. Adjusts model_weights table.

## Event subscriptions

- `forecast:trajectory-computed`
- `market:bar-closed`

## Event publications

- `learning:prediction-scored`
- `learning:weight-adjusted`

## Plugin dependencies

- (none)

## Implementation status

- [x] Scaffold
- [ ] Implementation (STEP 4)
- [ ] Tests (STEP 4)
