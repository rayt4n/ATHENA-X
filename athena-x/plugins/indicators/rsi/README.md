# Relative Strength Index Plugin

| Field | Value |
|---|---|
| ID | `indicators.rsi` |
| Type | indicator |
| Runtime | python |
| Inputs | ['closes'] |
| Params | {'period': 14} |
| Outputs | ['value', 'signal'] |

## Description

Computes relative strength index values for a given series.

## Usage

Loaded by `engines/plugin-engine/` and consumed by the corresponding
TA agent under `agents/raw-intelligence/technical-analysis/rsi/`.

Implementation comes in STEP 4.
