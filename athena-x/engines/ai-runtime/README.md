# AI Runtime (GPU)

GPU inference server for heavy models (Change 4):
PyTorch (LSTM, Transformer), TabPFN, XGBoost, CatBoost, LightGBM-large.
Loads models at startup, keeps them warm in GPU memory, batches requests.
LSTM and Transformer NEVER run in the browser — this engine owns them.

## Implementation status

- [x] Scaffold
- [ ] Implementation (STEP 4)
- [ ] Tests (STEP 4)
