# Average True Range Plugin

| Field | Value |
|---|---|
| ID | `indicators.atr` |
| Type | indicator |
| Runtime | python |
| Inputs | ['highs', 'lows', 'closes'] |
| Params | {'period': 14} |
| Outputs | ['value'] |

## Description

Computes average true range values for a given series.

## Usage

Loaded by `engines/plugin-engine/` and consumed by the corresponding
TA agent under `agents/raw-intelligence/technical-analysis/atr/`.

Implementation comes in STEP 4.
