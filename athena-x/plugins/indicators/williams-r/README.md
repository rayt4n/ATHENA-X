# Williams %R Plugin

| Field | Value |
|---|---|
| ID | `indicators.williams-r` |
| Type | indicator |
| Runtime | python |
| Inputs | ['highs', 'lows', 'closes'] |
| Params | {'period': 14} |
| Outputs | ['value'] |

## Description

Computes williams %r values for a given series.

## Usage

Loaded by `engines/plugin-engine/` and consumed by the corresponding
TA agent under `agents/raw-intelligence/technical-analysis/williams-r/`.

Implementation comes in STEP 4.
