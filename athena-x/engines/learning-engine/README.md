# Self-Correction Engine

Continuously scores predictions vs actuals (Change 12):
prediction → market outcome → compare → error → weight adjustment → improve.
Maintains model_weights table in ai_intelligence schema.
Adjustments are consumed by Supervisor (Change 3) and Forecast Ensemble.

## Implementation status

- [x] Scaffold
- [ ] Implementation (STEP 4)
- [ ] Tests (STEP 4)
