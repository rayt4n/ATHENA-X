# AI Model Schemas

Input/output contracts for every AI model in the registry.

Used by:
- `engines/ai-runtime/` — to validate inference requests/responses
- `engines/onnx-runtime/` — to validate browser-runnable models
- `engines/learning-engine/` — to score predictions against outcomes

## Routing table (non-overridable)

| Model ID | Runtime | Location |
|---|---|---|
| `lstm` | python-gpu | Python backend (PyTorch) |
| `transformer` | python-gpu | Python backend (PyTorch) |
| `tabpfn` | python-gpu | Python backend |
| `xgboost` | python-gpu | Python backend |
| `catboost` | python-gpu | Python backend |
| `lightgbm-large` | python-gpu | Python backend |
| `lightgbm-small` | browser-onnx | Frontend (onnxruntime-web) |
| `random-forest` | browser-onnx | Frontend (onnxruntime-web) |
| `logistic` | browser-onnx | Frontend (onnxruntime-web) |

**LSTM and Transformer NEVER run in the browser.**
