# database/

Four logical databases (Change 14). Implemented as four Postgres schemas
in a single Supabase instance for dev/staging, optionally separate clusters
in production.

## Layout

```
database/
├── raw-market-data/         # Schema: raw_market_data — untouched provider output
├── processed-market-data/   # Schema: processed_market_data — normalized + validated
├── ai-intelligence/         # Schema: ai_intelligence — agent outputs, predictions, weights
├── historical-reports/      # Schema: historical_reports — reports + backtests
├── migrations/              # Supabase migrations (timestamped)
├── seeds/                   # Dev seed data
└── policies/                # Row-level security policies
```

## Writer access (enforced by RLS)

| Schema | Writer |
|---|---|
| `raw_market_data` | `collection-agent` only (service role) |
| `processed_market_data` | `standardization-agent` only (service role) |
| `ai_intelligence` | Each agent writes only to its own tables |
| `historical_reports` | `report-engine` + `validator-engine` |

Reader access is open to all authenticated users (subject to user RLS).
