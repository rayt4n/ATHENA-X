# ADR-0004: Dashboard Never Calculates

## Status
Accepted

## Context
The original Space site computed everything client-side. This caused
inconsistencies between modules, made the dashboard heavy, and prevented
server-side auditing of calculations.

## Decision
The Next.js dashboard performs ZERO calculations. It only:
- Display, Filter, Search, Layout, User interaction

All calculations happen in the Python backend. The dashboard consumes
results via TanStack Query (for request-response) and bus subscriptions
(for real-time updates).

Enforced by a custom ESLint rule (`@athena-x/no-calc-in-dashboard`) that
bans arithmetic operators and Math.* calls in dashboard components.

## Consequences
- Pros: single source of truth for calculations, auditable, dashboard stays light
- Cons: more network round-trips
- Mitigation: TanStack Query caching + bus subscriptions for real-time
