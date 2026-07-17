# Volume-Weighted Average Price Plugin

| Field | Value |
|---|---|
| ID | `indicators.vwap` |
| Type | indicator |
| Runtime | python |
| Inputs | ['highs', 'lows', 'closes', 'volumes'] |
| Params | {} |
| Outputs | ['value', 'signal'] |

## Description

Computes volume-weighted average price values for a given series.

## Usage

Loaded by `engines/plugin-engine/` and consumed by the corresponding
TA agent under `agents/raw-intelligence/technical-analysis/vwap/`.

Implementation comes in STEP 4.
