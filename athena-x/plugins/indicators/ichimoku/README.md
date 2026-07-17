# Ichimoku Cloud Plugin

| Field | Value |
|---|---|
| ID | `indicators.ichimoku` |
| Type | indicator |
| Runtime | python |
| Inputs | ['highs', 'lows', 'closes'] |
| Params | {} |
| Outputs | ['tenkan', 'kijun', 'senkou_a', 'senkou_b', 'chikou'] |

## Description

Computes ichimoku cloud values for a given series.

## Usage

Loaded by `engines/plugin-engine/` and consumed by the corresponding
TA agent under `agents/raw-intelligence/technical-analysis/ichimoku/`.

Implementation comes in STEP 4.
