# On-Balance Volume Plugin

| Field | Value |
|---|---|
| ID | `indicators.obv` |
| Type | indicator |
| Runtime | python |
| Inputs | ['closes', 'volumes'] |
| Params | {} |
| Outputs | ['value'] |

## Description

Computes on-balance volume values for a given series.

## Usage

Loaded by `engines/plugin-engine/` and consumed by the corresponding
TA agent under `agents/raw-intelligence/technical-analysis/obv/`.

Implementation comes in STEP 4.
