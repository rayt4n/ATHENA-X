# Commodity Channel Index Plugin

| Field | Value |
|---|---|
| ID | `indicators.cci` |
| Type | indicator |
| Runtime | python |
| Inputs | ['highs', 'lows', 'closes'] |
| Params | {'period': 20} |
| Outputs | ['value'] |

## Description

Computes commodity channel index values for a given series.

## Usage

Loaded by `engines/plugin-engine/` and consumed by the corresponding
TA agent under `agents/raw-intelligence/technical-analysis/cci/`.

Implementation comes in STEP 4.
