# ADR-0005: Supervisor-Governed Agents

## Status
Accepted

## Context
With 77+ AI agents running concurrently, conflicts are inevitable
(e.g., TA bullish + News bearish). Without coordination, the system
would produce contradictory outputs.

## Decision
Every agent reports to a Supervisor AI. The Supervisor:
- Detects conflicting signals
- Checks stale data
- Detects failing agents (no heartbeat)
- Triggers retries (max 3, exponential backoff)
- Performs confidence weighting (dynamically adjusted based on accuracy)
- Delegates report generation
- Runs self-learning (adjusts weights from outcomes)
- Tracks performance statistics

## Consequences
- Pros: coherent system behavior, graceful degradation, continuous improvement
- Cons: Supervisor is a single point of failure (mitigated by health monitoring)
- Mitigation: Supervisor itself is supervised by health-monitor + restart policy
