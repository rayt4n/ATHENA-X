# STEP 4 — Stage 4 Plan (Institutional Specification v2.0, Approved)

> **Status**: Approved with enhancements.
> **Stage 3 status**: ✅ Complete (315/315 tests pass).
> **Stage 4 purpose**: Transform validated data into a single canonical format
> independent of data providers.

---

## 0. Approval Gate

User's verbatim directive:

> "From this stage onward, no downstream module may reference provider-specific
> field names or formats... Only the designated standardization agents can write
> to the canonical databases... Replay from raw payload → validation →
> standardization is deterministic and reproducible... I would also require a
> Schema Registry service."

---

## 1. The 8-Stage Standardization Pipeline

```
Validated Record
        │
        ▼
1. Symbol Standardization         (BRK-B → BRK.B)
        │
        ▼
2. Timezone Standardization       (UTC + exchange local + session + trading day)
        │
        ▼
3. Market Calendar Standardization (NYSE, NASDAQ, CME, CBOE, FX, Crypto)
        │
        ▼
4. Unit Standardization           (cents → dollars, % → decimal)
        │
        ▼
5. Field Mapping                   (close/last/price → last_price)
        │
        ▼
6. Precision Standardization      (asset-class-specific decimals)
        │
        ▼
7. Asset Classification           (asset_class, market, exchange, sector, region, currency)
        │
        ▼
8. Canonical Schema Builder       (assembles final MarketRecord / OptionsRecord / etc.)
        │
        ▼
Canonical Database
```

---

## 2. The 4 Standardization Agents

### 2.1 Market Standardization Agent

**Responsible for**: Equities, ETFs, Futures, Indices, FX, Commodities

### 2.2 Options Standardization Agent

**Responsible for**: Option chains, Greeks, Expirations, Strikes, Option metadata

**Rule**: No calculations.

### 2.3 News Standardization Agent

**Normalize**: Sources, Categories, Symbols, Languages, URLs, Publication timestamps

**Rule**: No sentiment.

### 2.4 Macro Standardization Agent

**Normalize**: Economic releases, Treasury data, Fed announcements, Employment,
Inflation, GDP, PMI

---

## 3. Symbol Normalization

Create one canonical symbol dictionary.

Examples:
- `SPY`, `SPY.US`, `NYSEARCA:SPY` → `SPY`
- `ESU26`, `ES1!`, `ES` → `ES`
- `BRK-B`, `BRK.B` → `BRK.B`

Maintain aliases for every provider.

---

## 4. Time Standardization

Every timestamp should contain:
- UTC timestamp
- Exchange local time
- Session
- Trading day
- ISO-8601 format
- Nanosecond precision if available

**Never lose the original provider timestamp.**

---

## 5. Market Calendar Normalization

Support:
- NYSE
- NASDAQ
- CME
- CBOE
- FX (24/5)
- Crypto (24/7)

Include:
- Holidays
- Half-days
- Early closes
- DST transitions

---

## 6. Unit Normalization

Examples:
- `15025` cents → `150.25` USD

Standardize:
- Currency
- Percentages
- Basis points
- Volume units
- Time units

---

## 7. Field Mapping

Every provider field maps into canonical names.

Example:
- `close`, `Close`, `last`, `lastPrice`, `price` → `last_price`

Canonical names:
- `open`, `high`, `low`, `close`, `last_price`, `bid`, `ask`, `volume`
- `open_interest`, `implied_volatility`, `delta`, `gamma`, `theta`, `vega`

---

## 8. Precision Rules

Define precision by asset class.

Examples:
- asset: SPY, precision: 2 decimals

**Precision should be configurable, not hard-coded.**

---

## 9. Asset Classification

Each record receives:
- `asset_class`
- `market`
- `exchange`
- `sector`
- `industry`
- `region`
- `currency`

---

## 10. Canonical Schema

Every downstream AI receives the same structure regardless of source.

Example:
```
MarketRecord
├── symbol
├── asset_class
├── exchange
├── timestamp
├── session
├── open
├── high
├── low
├── close
├── last_price
├── volume
├── provider_metadata
└── validation_metadata
```

**No downstream component should need provider-specific logic.**

---

## 11. Versioning

Each record should include:
- `schema_version` (canonical schema version)
- `mapping_version` (field mapping version)
- `provider_version` (provider adapter version)

This allows safe schema evolution over time.

---

## 12. Provenance

Every standardized record should reference:
- `source_provider`
- `raw_payload_id`
- `validation_id`
- `transformation_id`

This ensures complete traceability from analysis back to the original data.

---

## 13. Schema Registry (additional req)

A centralized service where every AI agent retrieves canonical schemas.

Benefits:
- Add new providers, asset classes, or data fields with minimal changes
- All modules stay synchronized as the platform evolves
- Establishes a stable contract between data platform and analytics

---

## 14. Database Write Rule

The four standardization agents are the **only writers** to the canonical Layer 4
databases. All other components access data through APIs or events.

---

## 15. Stage 4 Exit Criteria

Stage 4 is complete only when:

1. ✅ All validated records transformed into a single canonical schema
2. ✅ Symbol aliases resolved consistently across providers
3. ✅ Timezones, sessions, trading calendars standardized
4. ✅ Units and precision follow configurable asset-class rules
5. ✅ Provider-specific field names fully mapped to canonical names
6. ✅ Schema versioning and provenance attached to every record
7. ✅ Only designated standardization agents write to canonical databases
8. ✅ All downstream services consume standardized data without provider-specific code
9. ✅ Replay from raw payload → validation → standardization is deterministic and reproducible
10. ✅ Unit, integration, replay, migration, schema compatibility tests all pass

---

## 16. Acceptance Tests (8 categories — adds migration + schema compat)

1. **Functional** — each standardization step works correctly
2. **Integration** — pipeline orchestrates all 8 steps
3. **Data accuracy** — canonical records match expected output
4. **Stress** — high throughput through standardization
5. **Failover** — provider-specific quirks handled gracefully
6. **Performance** — <2ms standardization latency per record
7. **Replay** — deterministic (same raw + version → same canonical)
8. **Migration** — schema versioning works (old records still readable)
9. **Schema compatibility** — Schema Registry serves correct schemas

---

## 17. Implementation Plan

### New packages

| Package | Purpose |
|---|---|
| `runtime/schema-registry/` | Centralized canonical schema registry |
| `runtime/canonical-types/` | Canonical record types (MarketRecord, OptionsRecord, etc.) |
| `runtime/symbol-dictionary/` | Symbol alias resolution |
| `runtime/market-calendars/` | NYSE/NASDAQ/CME/CBOE/FX/Crypto calendar configs |
| `agents/standardization/_base/` | BaseStandardizer + StandardizationPipeline |
| `agents/standardization/market/` | Market Standardization Agent |
| `agents/standardization/options/` | Options Standardization Agent |
| `agents/standardization/news/` | News Standardization Agent |
| `agents/standardization/macro/` | Macro Standardization Agent |
| `runtime/stage4-integration/` | DI wiring + 8-category acceptance tests |

---

**Approval**: Approved. Proceeding with implementation.
