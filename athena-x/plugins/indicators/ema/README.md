# Exponential Moving Average Plugin

| Field | Value |
|---|---|
| ID | `indicators.ema` |
| Type | indicator |
| Runtime | python |
| Inputs | ['closes'] |
| Params | {'period': 20} |
| Outputs | ['value', 'signal'] |

## Description

Computes exponential moving average values for a given series.

## Usage

Loaded by `engines/plugin-engine/` and consumed by the corresponding
TA agent under `agents/raw-intelligence/technical-analysis/ema/`.

Implementation comes in STEP 4.
