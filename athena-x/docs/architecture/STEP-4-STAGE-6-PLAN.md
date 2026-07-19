# STEP 4 — Stage 6 Plan (Event Bus as Central Nervous System, Enhanced)

> **Status**: Approved with enhancements.
> **Stage 5.1 status**: ✅ Complete (498 tests, stage-gate 6/6 PASS, modularity audit 0 violations).
> **Stage 6 purpose**: Build a high-throughput, event-driven communication layer where
> **every AI agent communicates only through standardized events**.

---

## 0. Approval Gate

User's verbatim directive:

> "The Event Bus should not just be a transport layer—it should become the central
> nervous system of ATHENA-X... No direct agent-to-agent calls. No direct
> module-to-module calls. Everything communicates through events."

---

## 1. The 5 Event Categories

| Category | Events | Purpose |
|---|---|---|
| **market** | `market:raw`, `market:validated`, `market:canonical`, `market:updated`, `market:closed` | Market data lifecycle |
| **options** | `options:chain`, `options:flow`, `options:oi`, `options:greeks`, `options:iv`, `options:gex` | Options data |
| **news** | `news:breaking`, `news:macro`, `news:earnings`, `news:mag7` | News by category |
| **ai** | `ai:technical`, `ai:forecast`, `ai:probability`, `ai:validation`, `ai:consensus` | AI agent outputs |
| **reports** | `report:started`, `report:partial`, `report:completed` | Report lifecycle |
| **system** | `system:heartbeat`, `system:error`, `system:warning`, `system:provider`, `system:health` | Infrastructure |

---

## 2. Standard Event Envelope (10 mandatory fields)

Every event has the same structure:

```json
{
  "event_id": "uuid",
  "event_type": "market:raw",
  "source_agent": "data-collection.yahoo",
  "correlation_id": "uuid",
  "symbol": "ES",
  "timestamp": "2026-07-18T09:30:01.250Z",
  "schema_version": "1.0.0",
  "priority": "high",
  "processing_time_ms": 5,
  "payload": {}
}
```

This makes debugging, replay, and tracing much easier.

---

## 3. Event Priority (4 levels)

| Priority | Examples | Backpressure |
|---|---|---|
| **critical** | Provider failure, trading halt, market disconnect | Never dropped |
| **high** | ES tick, option flow, VIX update | Keep latest if behind |
| **normal** | News, earnings, macro | Queue (bounded) |
| **low** | Health checks, logs, metrics | Coalesce into summaries |

Under heavy load, low-priority events can be delayed without affecting trading intelligence.

---

## 4. Correlation IDs (end-to-end tracing)

Every event generated from the same market snapshot shares a correlation ID.

```
Correlation: 2026-07-18T09:30:01.250Z
  ↓
ES Tick → SPY Update → Option Chain → Technical Analysis → Forecast → Dashboard
```

This allows tracing an entire processing pipeline from one market update.

---

## 5. Snapshot Coordinator (barrier)

Prevents mixing stale and fresh data.

```
ES updated 09:30:01
SPY updated 09:30:02
VIX updated 09:29:57  ← stale
```

If TA AI runs immediately, it may combine inconsistent inputs.

**Solution**: Snapshot Coordinator waits for required data within a configurable
time window before publishing a synchronized snapshot.

- If a required feed is stale beyond threshold → mark snapshot as **degraded** or **block** (configurable).
- Publishes `market:snapshot` event with all synchronized feeds.

---

## 6. Backpressure Policies (refined)

| Event type | Policy |
|---|---|
| Market ticks | Keep only the latest if consumers fall behind |
| News and macro | Never drop; queue them |
| Orders/execution (future) | Never drop |
| Health metrics | Coalesce multiple updates into summaries |

Keeps latency low while preserving critical information.

---

## 7. Event Replay

Every event is written to the event log.

```
09:30 → 09:31 → 09:32 → 09:33
```

Later you can replay any time range. Invaluable for debugging and backtesting.

- Event log is append-only
- Deterministic replay (same events → same outcomes)
- Supports time-range queries

---

## 8. Event Monitoring Dashboard

Internal dashboard showing:

- Events/sec
- Queue depth
- Average latency
- Slowest consumers
- Dropped events
- Failed events
- Retry count
- Dead-letter queue size
- Active agents
- Provider latency

Visible to Supervisor AI and developers.

---

## 9. WebSocket Bridge

Mirrors backend events to frontend in real time.

- Frontend subscribes via WebSocket
- Pattern-based subscriptions (e.g., `market:*`, `ai:forecast`)
- Backpressure: drop stale market data >500ms on frontend side
- Connection management (auto-reconnect)

---

## 10. Stage 6 Exit Criteria

Stage 6 is complete only when:

1. ✅ All agents communicate exclusively through the Event Bus
2. ✅ Every event conforms to the standard event envelope
3. ✅ Schema validation rejects malformed events
4. ✅ Correlation IDs enable full end-to-end tracing
5. ✅ The Snapshot Coordinator prevents inconsistent multi-source analysis
6. ✅ Priority queues and backpressure policies behave as designed
7. ✅ Event replay reproduces historical event streams accurately
8. ✅ Event monitoring reports latency, throughput, failures, and dropped events
9. ✅ WebSocket mirroring updates the frontend in real time
10. ✅ All six stage-gate criteria pass

---

## 11. Implementation Plan

### New packages

| Package | Purpose |
|---|---|
| `runtime/event-envelope/` | Standard event envelope (10 fields) + priority + correlation |
| `runtime/event-priority/` | 4-level priority queue (critical/high/normal/low) |
| `runtime/event-correlation/` | Correlation ID propagation + tracing |
| `runtime/snapshot-coordinator/` | Barrier — waits for synchronized feeds |
| `runtime/event-backpressure/` | Per-category backpressure policies |
| `runtime/event-log/` | Append-only event log + replay |
| `runtime/event-monitoring/` | Dashboard metrics (events/sec, queue depth, etc.) |
| `runtime/websocket-bridge/` | Frontend real-time mirroring |
| `runtime/stage6-integration/` | End-to-end wiring + 9-category acceptance tests |

### Updates to existing packages

- `runtime/event-bus/` — upgraded to use standard envelope + priority queues
- `schemas/events/` — updated with 5 categories + new event types

---

**Approval**: Approved. Proceeding with implementation.
