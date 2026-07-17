# Stochastic Oscillator Plugin

| Field | Value |
|---|---|
| ID | `indicators.stochastic` |
| Type | indicator |
| Runtime | python |
| Inputs | ['highs', 'lows', 'closes'] |
| Params | {'k_period': 14, 'd_period': 3} |
| Outputs | ['k', 'd'] |

## Description

Computes stochastic oscillator values for a given series.

## Usage

Loaded by `engines/plugin-engine/` and consumed by the corresponding
TA agent under `agents/raw-intelligence/technical-analysis/stochastic/`.

Implementation comes in STEP 4.
