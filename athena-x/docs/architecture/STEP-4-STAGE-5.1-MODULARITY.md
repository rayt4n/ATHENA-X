# STEP 4 — Stage 5.1: Modularity Rules + Stage-Gate Checklist

> **Status**: Approved as addition to Stage 5.
> **Applies to**: All stages going forward (Stage 6+).
> **Purpose**: Every component exposes a stable interface from day one. Plugin
> architecture allows adding new providers, indicators, or AI models without
> changing the rest of the system.

---

## 0. Approval Gate

User's verbatim directive:

> "Although I would postpone the advanced infrastructure, I would not postpone
> modularity. Every component should expose a stable interface from day one...
> This lets you plug in new providers, indicators, or AI models later without
> changing the rest of the system. From here onward, every stage should satisfy
> these rules before moving to the next."

---

## 1. The Plugin Interface Pattern

Every major component category exposes a **stable interface** (Protocol) from
day one. Concrete implementations plug into the interface. New implementations
can be added without changing consumers.

### 1.1 MarketDataProvider

```
MarketDataProvider (Protocol)
├── YahooProvider
├── FinnhubProvider
├── PolygonProvider
├── FlashAlphaProvider
├── FREDProvider
├── AlphaVantageProvider
├── DatabentoProvider
├── TradingEconomicsProvider
├── ReutersProvider
├── CNNProvider
├── WSJProvider
├── CNBCProvider
├── SECProvider
├── PolymarketProvider
└── FutureProvider  ← can be added without changing consumers
```

**Status**: ✅ Already implemented in Stage 2 (`providers/base/` defines
`MarketDataProvider` Protocol; 15 concrete implementations exist).

### 1.2 TechnicalIndicator

```
TechnicalIndicator (Protocol)
├── EMA
├── RSI
├── MACD
├── SMA
├── VWAP
├── ADX
├── ATR
├── BollingerBands
├── Fibonacci
├── Stochastic
├── CCI
├── WilliamsR
├── Ichimoku
├── OBV
└── FutureIndicator  ← can be added without changing consumers
```

**Status**: 🟡 To be formalized in Stage 7 (TA Engine). The plugin scaffolding
exists in `plugins/indicators/` but the stable `TechnicalIndicator` Protocol
needs to be promoted to a first-class interface.

### 1.3 ForecastModel

```
ForecastModel (Protocol)
├── ARIMA
├── LSTM
├── Transformer
├── XGBoost
├── LightGBM
├── CatBoost
├── TabPFN
├── RandomForest
├── LogisticRegression
└── FutureModel  ← can be added without changing consumers
```

**Status**: 🟡 To be formalized in Stage 11 (Forecast Engine).

### 1.4 Other Plugin Interfaces (existing + planned)

| Interface | Package | Status |
|---|---|---|
| `MarketDataProvider` | `providers/base/` | ✅ Stage 2 |
| `BaseValidator` | `agents/validation/_base/` | ✅ Stage 3 |
| `BaseStandardizer` | `agents/standardization/_base/` | ✅ Stage 4 |
| `MarketRepository` | `runtime/repository-interface/` | ✅ Stage 5 |
| `OptionsRepository` | `runtime/repository-interface/` | ✅ Stage 5 |
| `NewsRepository` | `runtime/repository-interface/` | ✅ Stage 5 |
| `MacroRepository` | `runtime/repository-interface/` | ✅ Stage 5 |
| `TechnicalIndicator` | `plugins/indicators/_base/` | 🟡 Stage 7 |
| `ForecastModel` | `engines/ai-runtime/` | 🟡 Stage 11 |
| `BaseCollector` | `agents/data-collection/_base/` | ✅ Stage 2 |
| `BusClient` | `runtime/event-bus/` | ✅ Stage 1 |
| `BaseAgent` | `agents/_base/` (to be created) | 🟡 Stage 6 |

---

## 2. The 6 Mandatory Stage-Gate Criteria

**From Stage 6 onward**, every stage MUST satisfy ALL 6 criteria before
proceeding to the next. No exceptions.

### 2.1 Functional

> Does it work correctly?

- All features behave as specified
- Acceptance tests pass (functional, integration, data accuracy)
- Edge cases handled (empty input, malformed data, concurrent access)

### 2.2 Tested

> Unit, integration, and end-to-end tests pass.

- **Unit tests**: ≥80% line coverage on services/business logic
- **Integration tests**: cross-package flows work end-to-end
- **E2E tests**: full pipeline (provider → validation → standardization → DB → consumer)
- **Replay tests**: deterministic (same input → same output)
- **Stress tests**: handles 10× expected peak load
- **Failover tests**: graceful degradation on component failure
- **Performance tests**: within latency/throughput budgets

### 2.3 Modular

> No circular dependencies; public interfaces only.

- **No circular imports** — verified by import graph analysis
- **Public interfaces only** — components consume other components through
  their public façade (`index.ts` / `__init__.py`), never internal files
- **Dependency direction** — lower layers never import higher layers:
  ```
  types ← providers ← collectors ← validators ← standardizers ← repositories ← agents
  ```
- **Plugin architecture** — new implementations can be added without changing
  consumers (via Protocol interfaces)
- **ESLint enforcement** — `import/no-boundaries` + `import/no-cycle` rules

### 2.4 Documented

> README, API, and event contracts are complete.

- **README.md** in every package — purpose, public API, usage examples
- **API docs** — every public function/class has a docstring
- **Event contracts** — every event type is documented in `schemas/events/`
- **Architecture Decision Records (ADRs)** — major decisions recorded in `docs/decisions/`
- **Runbooks** — operational guides in `docs/runbooks/`

### 2.5 Verifiable

> Inputs, outputs, logs, and health checks can be inspected.

- **Inputs** — every component accepts typed inputs (Pydantic models or Protocol)
- **Outputs** — every component produces typed outputs
- **Logs** — structured JSON logs with correlation IDs
- **Health checks** — every component exposes `/health` or `health_check()` method
- **Metrics** — performance metrics exposed for Supervisor dashboard
- **Audit trail** — every decision logged (validation, standardization, DB writes)

### 2.6 Production-ready

> CI/CD, linting, type checks, and builds all pass.

- **Type checks** — `mypy` (Python) / `tsc --noEmit` (TypeScript) pass with zero errors
- **Linting** — `ruff check` (Python) / `next lint` (TypeScript) pass with zero errors
- **Builds** — `hatch build` (Python) / `next build` (TypeScript) succeed
- **CI/CD** — GitHub Actions workflows pass on every PR
- **No TODOs** — no `TODO`, `FIXME`, `HACK` comments in production code
- **No dead code** — no unused imports, functions, or variables
- **No hardcoded values** — all magic numbers in config files

---

## 3. Stage-Gate Checklist Utility

A utility script that verifies all 6 criteria for a given stage.

**Location**: `tools/stage-gate-checklist/`

**Usage**:
```bash
python tools/stage-gate-checklist/check.py --stage 6
```

**Output**: Pass/Fail for each of the 6 criteria, with detailed evidence.

---

## 4. Modularity Audit (Retroactive on Stages 1–5)

### 4.1 Circular Dependency Check

Run `import` graph analysis on all Python packages. Verify no cycles.

### 4.2 Public Interface Audit

Verify every package exposes a public `__init__.py` with documented exports.
Internal files should not be importable outside the package.

### 4.3 Dependency Direction Audit

Verify the dependency graph flows in one direction:
```
runtime/types ← runtime/event-bus ← providers ← collectors
  ← validators ← standardizers ← repositories ← agents
```

No arrow should point backwards.

### 4.4 Plugin Interface Audit

Verify each plugin category has a Protocol interface:
- MarketDataProvider ✅
- BaseValidator ✅
- BaseStandardizer ✅
- MarketRepository ✅
- TechnicalIndicator 🟡 (Stage 7)
- ForecastModel 🟡 (Stage 11)

---

## 5. V2 Deferral

The following are explicitly **deferred to V2** (after V1 is complete and
generating accurate real-time market intelligence and reports):

| V2 Feature | Reason for deferral |
|---|---|
| Feature Store | V1 uses direct DB reads; Feature Store adds complexity |
| TimescaleDB / ClickHouse | V1 uses Postgres; Repository Interface allows migration |
| Distributed processing (Spark/Flink) | V1 is single-node; asyncio + Web Workers suffice |
| Advanced AI infrastructure (Ray, Kubeflow) | V1 uses local GPU; cloud orchestration is V2 |
| Multi-region replication | V1 is single-region; DR design allows addition |
| Real-time streaming (Kafka) | V1 uses Redis Pub/Sub; upgrade path is V2 |

**V1 goal**: Accurate real-time market intelligence + 1-minute institutional reports.

---

## 6. Impact on Stage 6+

Stage 6 (Event Bus) and all subsequent stages will:

1. Define stable Protocol interfaces before implementation
2. Ship with README + API docs + event contracts
3. Pass all 6 stage-gate criteria before proceeding
4. Use the stage-gate checklist utility for verification
5. Follow the plugin architecture pattern

---

**Approval**: Approved. Proceeding to implement the stage-gate checklist + modularity audit, then Stage 6.
