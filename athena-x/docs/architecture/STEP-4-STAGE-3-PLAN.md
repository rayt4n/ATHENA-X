# STEP 4 — Stage 3 Plan (Enhanced, User-Approved)

> **Status**: Approved with enhancements.
> **Stage 2 status**: ✅ Complete (197/197 tests pass).
> **Stage 3 purpose**: Build a multi-stage validation pipeline with 11 specialized validator agents. **Nothing reaches the canonical database until validated.**

---

## 0. Approval Gate

User's verbatim directive:

> "Instead of one validator, build specialized agents... Never just pass/fail...
> Never delete rejected data... Nothing should be 'silently fixed'...
> The validator must be deterministic... This synchronization layer will
> significantly improve the reliability of your future decision engine."

The 11 validators + pipeline + quarantine + audit trail are non-negotiable.

---

## 1. The 10-Stage Validation Pipeline

```
Provider
    │
    ▼
1. Schema Validation          → reject malformed
    │
    ▼
2. Timestamp Validation       → reject impossible timestamps
    │
    ▼
3. Market Calendar Validation → reject Christmas trades
    │
    ▼
4. Cross-Provider Validation  → consensus check
    │
    ▼
5. Market Logic Validation    → reject high<low, negative vol
    │
    ▼
6. Completeness Validation    → detect gaps
    │
    ▼
7. Duplicate Detection        → reject duplicates
    │
    ▼
8. Outlier Detection          → quarantine (MAD, Z-score)
    │
    ▼
9. Confidence Scoring         → 0.0–1.0
    │
    ▼
10. Quality Classification    → A+/A/B/C/D/F
    │
    ▼
Canonical Database (only Verified/Warning records)
```

Plus the additional **Market State Validator** (synchronization layer) that runs
before data is released to downstream analytics.

---

## 2. The 11 Validator Agents

### 2.1 Schema Validator
Verifies: required fields exist, data types, null values, numeric precision,
currency, exchange, symbol validity. Rejects malformed records immediately.

### 2.2 Timestamp Validator
Checks: UTC format, exchange timestamp, arrival timestamp, clock drift,
duplicate timestamps, out-of-order events. Rejects impossible timestamps.

### 2.3 Market Calendar Validator
Verifies: trading day, market holiday, weekend, session, early close,
half-day schedule. Example: SPY trading on Christmas → REJECT.

### 2.4 Cross-Provider Validator
Compares providers. Yahoo 752.44, Polygon 752.45, Finnhub 752.46 →
consensus 752.45. If another returns 742.00 → REJECT.

### 2.5 Market Logic Validator
Detects impossible values. High < Low, Close > High, Negative Volume,
Negative Open Interest, IV > 1000%, impossible Gamma. Reject.

### 2.6 Completeness Validator
Ensures: no missing bars, no missing option strikes, no missing expirations,
no missing Greeks, no missing timestamps. Detects gaps before storage.

### 2.7 Duplicate Detector
Rejects: same provider + same timestamp + same symbol + same payload.
Avoids duplicated events.

### 2.8 Outlier Detector
Uses robust statistical techniques: MAD (Median Absolute Deviation),
rolling Z-score, percent deviation from consensus, circuit breaker thresholds.
Outliers are **quarantined** rather than silently discarded.

### 2.9 Confidence Engine
Assigns every record a confidence score (0.0–1.0). Factors: provider
reliability, agreement with peers, freshness, latency, completeness,
historical provider accuracy. Example: Price 0.998, News 0.92, Dark Pool 0.75.

### 2.10 Quarantine Manager
Never deletes rejected data. Stores: reason, provider, raw payload,
timestamp, validator, error code. Supports debugging and auditing.

### 2.11 Market State Validator (additional)
Before data is released to downstream analytics, verifies all required feeds
for the current analysis are synchronized. Example: if SPY/ES/VIX/options are
at 10:15:01 but news is at 10:14:58 (3s stale), either delay publication
briefly or mark the dataset as partial. Prevents downstream AI from making
decisions on inconsistent snapshots — critical for intraday and 0DTE.

---

## 3. Validation Result Taxonomy

Every record receives one of 4 results (never just pass/fail):

| Result | Meaning | Action |
|---|---|---|
| `Verified` | Passed all checks, high confidence | Write to canonical DB |
| `Warning` | Passed with minor issues | Write to canonical DB + flag |
| `Quarantined` | Outlier or suspicious | Write to quarantine DB |
| `Rejected` | Failed critical check | Write to quarantine DB |

---

## 4. Confidence Metadata (6 fields, added to every record)

| Field | Type | Description |
|---|---|---|
| `validation_status` | enum | Verified / Warning / Quarantined / Rejected |
| `validation_time` | ISO 8601 UTC | When validation occurred |
| `validator_version` | semver | Pipeline version for replay determinism |
| `confidence_score` | float (0..1) | Computed by Confidence Engine |
| `provider_rank` | int | Provider's reliability rank (1=best) |
| `validation_reason` | string | Human-readable reason |
| `quality_grade` | enum | A+ / A / B / C / D / F |

---

## 5. Quality Grades

| Grade | Meaning | Confidence Range |
|---|---|---|
| `A+` | Institutional | ≥ 0.99 |
| `A` | Verified | ≥ 0.95 |
| `B` | Acceptable | ≥ 0.80 |
| `C` | Low Confidence | ≥ 0.60 |
| `D` | Quarantine | ≥ 0.30 |
| `F` | Reject | < 0.30 |

---

## 6. Audit Trail

Every validation decision is logged. Stored fields:

| Field | Description |
|---|---|
| `provider` | Source provider |
| `validator` | Which validator agent |
| `rule_triggered` | Specific rule that fired |
| `original_value` | The value as received |
| `corrected_value` | The value after correction (if any) |
| `timestamp` | When the decision was made |
| `version` | Validator version |
| `decision` | Verified / Warning / Quarantined / Rejected |

**Rule**: Nothing should be "silently fixed." Every correction is logged.

---

## 7. Replay Capability

The validator MUST be deterministic. Given the same raw payload and validator
version, it produces the same result every time. This is essential for:
- Backtesting (replay historical data through current validators)
- Debugging (reproduce a rejection)
- Auditing (prove a decision was correct at time T)

Implementation: validators are pure functions of (payload, context) → result.
No random, no time-dependent logic (use the payload's timestamp, not now()).

---

## 8. Self-Monitoring Metrics

Validation continuously reports:

| Metric | Description |
|---|---|
| `rejection_rate` | % of records rejected |
| `provider_error_rate` | % of failures per provider |
| `average_confidence` | Rolling avg confidence score |
| `validation_latency` | ms per validation |
| `quarantine_size` | Count of quarantined records |
| `missing_data_count` | Detected gaps |

The Supervisor AI (Stage 13) will consume these metrics.

---

## 9. Stage 3 Exit Criteria

Stage 3 is complete only when:

1. ✅ Every record passes the full validation pipeline before entering the canonical database
2. ✅ Malformed, duplicate, stale, incomplete, and outlier data are detected correctly
3. ✅ Cross-provider consensus and confidence scoring are operational
4. ✅ Quarantined records are retained with full audit trails
5. ✅ Validation is deterministic and replayable
6. ✅ Provider health metrics update automatically based on validation outcomes
7. ✅ Unit, integration, replay, failover, stress, and recovery tests all pass
8. ✅ The system demonstrates at least one full trading session with no invalid data entering the canonical database

---

## 10. Acceptance Tests (7 categories — adds replay)

1. **Functional** — each validator correctly verifies/rejects test data
2. **Integration** — pipeline orchestrates all 11 validators in order
3. **Data accuracy** — validated data matches provider consensus
4. **Stress** — 10,000 events/sec through validation pipeline
5. **Failover** — provider rejection triggers automatic failover
6. **Performance** — <2ms validation latency per event
7. **Replay** — same input + version → same output (determinism)

---

## 11. Implementation Plan

### 11.1 New packages

| Package | Purpose |
|---|---|
| `runtime/validation-types/` | Shared types (ValidationResult, QualityGrade, AuditEntry, QuarantineRecord) |
| `agents/validation/_base/` | BaseValidator framework + ValidationPipeline |
| `agents/validation/schema-validator/` | #1 |
| `agents/validation/timestamp-validator/` | #2 |
| `agents/validation/market-calendar-validator/` | #3 |
| `agents/validation/cross-provider-validator/` | #4 |
| `agents/validation/market-logic-validator/` | #5 |
| `agents/validation/completeness-validator/` | #6 |
| `agents/validation/duplicate-detector/` | #7 |
| `agents/validation/outlier-detector/` | #8 |
| `agents/validation/confidence-engine/` | #9 |
| `agents/validation/quarantine-manager/` | #10 |
| `agents/validation/market-state-validator/` | #11 (additional) |
| `runtime/audit-trail/` | Audit logging + replay |
| `runtime/stage3-integration/` | DI wiring + 7-category acceptance tests |

### 11.2 Dependency on Stages 1–2

Stage 3 builds on:
- `runtime/event-bus/` — for publishing validation events
- `runtime/institutional-metadata/` — for the 10 mandatory fields
- `runtime/session-awareness/` — for market calendar checks
- `runtime/raw-archival/` — for raw payload references in audit trail
- `runtime/data-freshness/` — for staleness checks
- `agents/data-collection/_base/` — collectors produce the records to validate

---

**Approval**: Approved. Proceeding with implementation.
