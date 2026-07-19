# Fibonacci Retracement Plugin

| Field | Value |
|---|---|
| ID | `indicators.fibonacci` |
| Type | indicator |
| Runtime | python |
| Inputs | ['highs', 'lows'] |
| Params | {'levels': [0.236, 0.382, 0.5, 0.618, 0.786]} |
| Outputs | ['levels'] |

## Description

Computes fibonacci retracement values for a given series.

## Usage

Loaded by `engines/plugin-engine/` and consumed by the corresponding
TA agent under `agents/raw-intelligence/technical-analysis/fibonacci/`.

Implementation comes in STEP 4.
