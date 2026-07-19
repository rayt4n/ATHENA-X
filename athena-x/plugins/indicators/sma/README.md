# Simple Moving Average Plugin

| Field | Value |
|---|---|
| ID | `indicators.sma` |
| Type | indicator |
| Runtime | python |
| Inputs | ['closes'] |
| Params | {'period': 50} |
| Outputs | ['value', 'signal'] |

## Description

Computes simple moving average values for a given series.

## Usage

Loaded by `engines/plugin-engine/` and consumed by the corresponding
TA agent under `agents/raw-intelligence/technical-analysis/sma/`.

Implementation comes in STEP 4.
