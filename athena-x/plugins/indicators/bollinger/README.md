# Bollinger Bands Plugin

| Field | Value |
|---|---|
| ID | `indicators.bollinger` |
| Type | indicator |
| Runtime | python |
| Inputs | ['closes'] |
| Params | {'period': 20, 'std_dev': 2} |
| Outputs | ['upper', 'middle', 'lower', 'percent_b'] |

## Description

Computes bollinger bands values for a given series.

## Usage

Loaded by `engines/plugin-engine/` and consumed by the corresponding
TA agent under `agents/raw-intelligence/technical-analysis/bollinger/`.

Implementation comes in STEP 4.
