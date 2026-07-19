# Average Directional Index Plugin

| Field | Value |
|---|---|
| ID | `indicators.adx` |
| Type | indicator |
| Runtime | python |
| Inputs | ['highs', 'lows', 'closes'] |
| Params | {'period': 14} |
| Outputs | ['adx', 'plus_di', 'minus_di'] |

## Description

Computes average directional index values for a given series.

## Usage

Loaded by `engines/plugin-engine/` and consumed by the corresponding
TA agent under `agents/raw-intelligence/technical-analysis/adx/`.

Implementation comes in STEP 4.
