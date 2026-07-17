# AI Forecast Engine

> Layer: **decision-intelligence**

Hybrid AI forecast ensemble (Change 4 of STEP 2). LSTM/Transformer/TabPFN/XGBoost/CatBoost/LightGBM-large → Python GPU; LightGBM-small/RF/Logistic → Browser ONNX. LSTM NEVER runs in browser.

## Event subscriptions

- `market:bar-closed`
- `decision:regime-classified`
- `learning:weight-adjusted`

## Event publications

- `forecast:trajectory-computed`
- `forecast:catalyst-detected`

## Plugin dependencies

- (none)

## Implementation status

- [x] Scaffold
- [ ] Implementation (STEP 4)
- [ ] Tests (STEP 4)
