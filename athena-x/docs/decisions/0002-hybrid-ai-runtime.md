# ADR-0002: Hybrid AI Runtime (Browser ONNX + Python GPU)

## Status
Accepted

## Context
Some AI models (LSTM, Transformer) require GPU and cannot run in browser.
Others (small tree ensembles, logistic regression) are trivial and should
run client-side for low latency.

## Decision
Implement a non-overridable routing table:
- LSTM, Transformer, TabPFN, XGBoost, CatBoost, LightGBM-large → Python GPU
- LightGBM-small, Random Forest, Logistic → Browser ONNX (onnxruntime-web)

LSTM and Transformer NEVER run in the browser. This is enforced by code,
not convention.

## Consequences
- Pros: optimal use of compute, predictable performance
- Cons: requires GPU instance for backend, model versioning complexity
- Mitigation: model registry + automated deployment
