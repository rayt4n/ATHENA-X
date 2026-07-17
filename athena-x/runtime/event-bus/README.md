# runtime/event-bus

Central nervous system of ATHENA-X. Every cross-agent and cross-module
communication flows through this bus.

## Topology

```
Frontend bus (TS, in-process)
       ↕ WebSocket bridge
Backend bus (Python, Redis Pub/Sub + NATS)
```

## Event metadata (mandatory — Change 11)

Every event MUST contain: eventId, eventType, timestamp, provider,
latency, confidence, dataVersion, retryCount, agentId, processingTime.

Events missing any field are rejected at the bus boundary.

## Usage (Python)

```python
from runtime.event_bus import BusClient, BusEvent

bus = BusClient(redis_url=..., nats_url=...)

await bus.publish(BusEvent(
    event_id=uuid4(),
    event_type="market:quote-updated",
    timestamp=datetime.utcnow().isoformat(),
    provider="yahoo",
    latency=12,
    confidence=0.98,
    data_version="1.0.0",
    retry_count=0,
    agent_id="data-collection.collection",
    processing_time=8,
    payload={"symbol": "NVDA", "last": 128.45, ...},
))

async def handler(event: BusEvent):
    ...

await bus.subscribe("market:quote-updated", handler)
```

## Usage (TypeScript — frontend mirror)

```typescript
import { useBusSubscription, publish } from '@athena-x/event-bus-browser';

useBusSubscription('market:quote-updated', (event) => {
  // update Zustand store
});
```
