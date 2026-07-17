# STEP 4 — Stage 5 Plan (Institutional Database Layer v2.0, Approved)

> **Status**: Approved with expansions.
> **Stage 4 status**: ✅ Complete (400/400 tests pass).
> **Stage 5 purpose**: Build a Bloomberg/Two Sigma-grade database platform —
> high-performance, auditable, replayable, modular.

---

## 0. Approval Gate

User's verbatim directive:

> "I would design it more like a Bloomberg/Two Sigma architecture rather than
> a typical CRUD application... No agent may write outside its assigned schema...
> I recommend abstracting the storage layer behind a Repository Interface now.
> This allows you to start with PostgreSQL/Supabase and later migrate hot
> time-series workloads to technologies like TimescaleDB or ClickHouse."

---

## 1. Database Architecture — 12 Schemas

Organized by **data lifecycle** (not feature).

| # | Schema | Purpose | Writer (exclusive) |
|---|---|---|---|
| 1 | `raw_landing` | Layer 1 raw provider payloads | Any Layer 1 provider adapter |
| 2 | `canonical_market` | Standardized market data | Market Standardization Agent ONLY |
| 3 | `canonical_options` | Standardized options data | Options Standardization Agent ONLY |
| 4 | `canonical_news` | Standardized news | News Standardization Agent ONLY |
| 5 | `canonical_macro` | Standardized macro | Macro Standardization Agent ONLY |
| 6 | `validation_db` | Validation decisions + quality scores | Validation Agents ONLY |
| 7 | `ai_intelligence` | TA/Options/News/Macro/Cross-Market signals | Intelligence Agents (each owns tables) |
| 8 | `forecast_db` | Decision agent outputs (regime, scenarios, forecasts) | Decision Agents ONLY |
| 9 | `historical_db` | Reports + backtests | Report Engine + Validator Engine ONLY |
| 10 | `market_replay_db` | Minute-by-minute cross-domain snapshots | Market Replay Recorder ONLY |
| 11 | `ai_memory_db` | Predictions + outcomes + lessons | Self-Correction Agents ONLY |
| 12 | `app` | User workspaces, watchlists, module instances | Frontend (via Supabase Auth + RLS) |

---

## 2. Writer-Lock Rule

Each schema has **exactly one** writing authority.

- Only Market Standardization AI writes to `canonical_market`
- Only Options Standardization AI writes to `canonical_options`
- Forecast AI never edits market data
- Dashboard never writes analytical results

**Enforcement**: dedicated database roles per agent.

| Role | Schema | Permissions |
|---|---|---|
| `role_market_standardizer` | `canonical_market` | INSERT, UPDATE (supersede) |
| `role_options_standardizer` | `canonical_options` | INSERT, UPDATE (supersede) |
| `role_news_standardizer` | `canonical_news` | INSERT |
| `role_macro_standardizer` | `canonical_macro` | INSERT |
| `role_validation` | `validation_db` | INSERT |
| `role_intelligence_*` | `ai_intelligence` | INSERT (own tables only) |
| `role_decision` | `forecast_db` | INSERT |
| `role_report_engine` | `historical_db` | INSERT |
| `role_replay_recorder` | `market_replay_db` | INSERT |
| `role_self_correction` | `ai_memory_db` | INSERT, UPDATE |
| `role_provider` | `raw_landing` | INSERT |
| `role_app_user` | `app` | SELECT, INSERT, UPDATE, DELETE (own rows) |

Everyone else has **read-only** access.

---

## 3. Row-Level Security (RLS)

Apply RLS across all user-facing schemas.

Policies enforce:
- **Per-user isolation** (user sees only their own rows)
- **Workspace isolation** (workspace members see workspace data)
- **Agent-specific service roles** (each agent role bypasses RLS for its schema)
- **Read/write permissions by responsibility**

Even internal AI agents use dedicated database roles.

---

## 4. Time-Series Partitioning

Large tables partitioned by year/month.

```
canonical_market.bars
├── 2026
│   ├── 07
│   ├── 08
│   └── 09
├── 2027
│   └── 01
```

For very high-frequency data (ticks, level2), use **daily partitions**.

Tables partitioned:
- `canonical_market.quotes` — monthly
- `canonical_market.bars` — monthly
- `canonical_market.trades` — daily
- `canonical_options.chains` — monthly
- `raw_landing.provider_payloads` — monthly
- `market_replay_db.minute_snapshots` — monthly
- `ai_memory_db.predictions` — monthly

---

## 5. Index Strategy

| Table | Index |
|---|---|
| `canonical_market.quotes` | (symbol, market_timestamp DESC) |
| `canonical_market.bars` | (symbol, timeframe, market_timestamp DESC) |
| `canonical_options.chains` | (symbol, expiry, strike) |
| `canonical_news.headlines` | (published_at DESC), (symbol, published_at DESC) |
| `validation_db.decisions` | (validator, symbol, decided_at DESC) |
| `ai_intelligence.ta_signals` | (agent_id, symbol, emitted_at DESC) |
| `forecast_db.trajectories` | (symbol, model_id, created_at DESC) |
| `historical_db.reports` | (user_id, created_at DESC) |
| `market_replay_db.minute_snapshots` | (trading_date, timestamp) |

**Avoid excessive indexing on write-heavy tables** (raw_landing, ticks).

---

## 6. Historical Replay

Every stage supports replay:

```
Raw Payload → Validation → Standardization → Analytics → Forecast
```

You can replay any trading day exactly as it occurred.

Implementation:
- Raw payloads archived (Stage 2 raw-archival)
- Validation deterministic (Stage 3 replay tests)
- Standardization deterministic (Stage 4 replay tests)
- Analytics + Forecast read from canonical databases

---

## 7. Immutable Records

**Do not update historical market records.**

If corrections needed:
1. Insert a corrected version
2. Mark the previous version as `superseded`
3. Maintain full audit history

Schema:
- Every record has `record_id` (UUID)
- Every record has `superseded_by` (UUID, nullable)
- Corrections insert a new record with `supersedes` pointing to the old
- The old record's `superseded_by` is updated to point to the new one

This preserves reproducibility.

---

## 8. Data Retention Policy

| Data type | Default retention | Action |
|---|---|---|
| Raw payloads | 1–2 years | Compress + archive to cold storage |
| Canonical market | Long-term | Keep forever (partitioned) |
| Forecasts | Long-term | Keep forever |
| Reports | User-defined | User controls deletion |
| Logs | 90–180 days | Auto-delete |
| Health metrics | Rolling window (30 days) | Auto-delete old |

Retention is **configurable** via `runtime/config/`.

---

## 9. Backup & Recovery

- Daily full backups
- Frequent incremental backups (every 15 min for market data)
- Point-in-time recovery (PITR)
- Restore verification in CI/CD

> "A backup is only useful if it has been successfully restored in testing."

---

## 10. Performance Monitoring

Track:
- Database latency (p50, p95, p99)
- Query execution time
- Insert throughput
- Storage growth
- Partition health
- Index usage
- Lock contention
- Connection pool utilization

Expose in Supervisor dashboard (Stage 13).

---

## 11. Event Sourcing

Every database write emits an event:
- `db:market-written`
- `db:options-written`
- `db:news-written`
- `db:forecast-written`
- `db:report-written`
- `db:backtest-written`

Downstream services subscribe — no polling.

---

## 12. Database Versioning

Maintain:
- Schema version (DDL version)
- Migration version (which migrations applied)
- Data version (semantic version of data format)

Every report records which versions were used.

---

## 13. Disaster Recovery

- Automatic failover
- Replica promotion
- Restore from backup
- Corruption detection
- Integrity verification

Design interfaces so replication can be added later (start with single DB).

---

## 14. Repository Interface (Strategic Recommendation)

Abstract the storage layer behind a Repository Interface.

```python
class MarketRepository(Protocol):
    async def write_quote(self, record: MarketRecord) -> str: ...
    async def read_quote(self, symbol: str) -> MarketRecord | None: ...
    async def query_bars(self, symbol, timeframe, start, end) -> list[Bar]: ...
    async def supersede(self, record_id: str, corrected: MarketRecord) -> str: ...
```

Implementations:
- `InMemoryMarketRepository` — for tests + dev (no DB required)
- `PostgresMarketRepository` — production (Supabase/Postgres)
- `TimescaleMarketRepository` — future (time-series optimized)
- `ClickHouseMarketRepository` — future (analytics optimized)

This allows migrating hot time-series workloads without changing AI agents.

---

## 15. Stage 5 Exit Criteria

Stage 5 is complete only when:

1. ✅ All 12 schemas implemented with clear ownership
2. ✅ Writer-lock rules enforced through database roles + RLS
3. ✅ Time-series partitioning operational for high-volume tables
4. ✅ Indexes support expected query patterns without degrading ingestion
5. ✅ Immutable data and audit trails enforced
6. ✅ Backup, restore, and replay successfully tested
7. ✅ Database health metrics available to Supervisor AI
8. ✅ Event notifications published for all writes
9. ✅ Migration, integrity, failover, and recovery tests pass
10. ✅ A full trading day can be ingested, stored, replayed, and restored without data loss

---

## 16. Acceptance Tests (9 categories)

1. **Functional** — each repository operation works
2. **Integration** — repositories wire into standardization agents
3. **Data accuracy** — written data matches read data
4. **Stress** — high write throughput (10,000 inserts/sec)
5. **Failover** — writer-lock enforcement (non-designated agent can't write)
6. **Performance** — <5ms write latency, <2ms read latency
7. **Replay** — immutable records + supersession works
8. **Migration** — schema versioning works
9. **Integrity** — corruption detection + verification
10. **Recovery** — backup + restore tested

---

## 17. Implementation Plan

### New packages

| Package | Purpose |
|---|---|
| `runtime/repository-interface/` | Abstract repository protocols (storage-agnostic) |
| `runtime/db-roles/` | Database role definitions + RLS policies |
| `runtime/db-partitioning/` | Partition management utilities |
| `runtime/db-events/` | Event sourcing (emit db:* events on writes) |
| `runtime/db-monitoring/` | Performance metrics + health checks |
| `runtime/db-backup/` | Backup + restore utilities |
| `runtime/in-memory-repository/` | In-memory implementation (tests + dev) |
| `runtime/stage5-integration/` | 9-category acceptance tests |

### Database schema files

Update `database/` with:
- Partitioned table DDL
- Index DDL
- RLS policies
- Role definitions
- Migration scripts

---

**Approval**: Approved. Proceeding with implementation.
