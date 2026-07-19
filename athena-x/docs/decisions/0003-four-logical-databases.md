# ADR-0003: Four Logical Databases

## Status
Accepted

## Context
The system processes data at different stages: raw provider output,
validated/standardized data, AI intelligence, and historical reports.
Mixing these creates query complexity and risks data contamination.

## Decision
Implement four logical databases (Postgres schemas in Supabase):
- `raw_market_data` — writer: collection-agent only
- `processed_market_data` — writer: standardization-agent only
- `ai_intelligence` — each agent writes only to its own tables
- `historical_reports` — writers: report-engine, validator-engine

Reader access is open to authenticated users (subject to user RLS).

## Consequences
- Pros: clear data lineage, no contamination, audit trail
- Cons: more tables, cross-schema joins needed for some queries
- Mitigation: dedicated views for cross-schema reads
