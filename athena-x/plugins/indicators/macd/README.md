# Moving Average Convergence Divergence Plugin

| Field | Value |
|---|---|
| ID | `indicators.macd` |
| Type | indicator |
| Runtime | python |
| Inputs | ['closes'] |
| Params | {'fast': 12, 'slow': 26, 'signal': 9} |
| Outputs | ['macd', 'signal', 'histogram'] |

## Description

Computes moving average convergence divergence values for a given series.

## Usage

Loaded by `engines/plugin-engine/` and consumed by the corresponding
TA agent under `agents/raw-intelligence/technical-analysis/macd/`.

Implementation comes in STEP 4.
