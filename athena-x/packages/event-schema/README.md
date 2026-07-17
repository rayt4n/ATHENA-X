# @athena-x/event-schema

Single source of truth for all event bus message schemas.

## Architecture

```
schemas/events/*.yaml  ──►  generate-ts.ts  ──►  types.ts (TypeScript)
                      └──►  generate-py.py  ──►  events.py (Pydantic)
```

Both the TypeScript frontend bus and the Python backend bus import generated
types from this package. Never hand-edit the generated files.

## Mandatory event metadata

Every event MUST contain these 8 fields (Change 11 of STEP 2.1):

- `eventId` (UUID)
- `eventType` (string, e.g., `"market:quote-updated"`)
- `timestamp` (ISO 8601 UTC)
- `provider` (string — source provider/agent)
- `latency` (ms — source to bus publish)
- `confidence` (0..1)
- `dataVersion` (semver of payload schema)
- `retryCount` (0 on first publish)
- `agentId` (emitting agent ID)
- `processingTime` (ms the agent spent producing this)

## Usage

```typescript
import type { BusEvent, MarketQuoteUpdated } from '@athena-x/event-schema';
```

```python
from athena_x_event_schema import BusEvent, MarketQuoteUpdated
```
