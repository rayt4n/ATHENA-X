# runtime/

Cross-cutting infrastructure shared by all agents and engines.

## Modules

| Module | Purpose |
|---|---|
| `event-bus/` | Typed pub/sub bus (Python + TypeScript mirrors) |
| `message-queue/` | Job queue (Redis Streams or NATS JetStream) |
| `scheduler/` | Cron + on-demand task scheduling |
| `health-monitor/` | Agent + provider health aggregation (Changes 17, 18) |
| `logger/` | Structured logger (Pino TS + Pio Py) |
| `metrics/` | Prometheus metrics exporter |
| `tracing/` | OpenTelemetry instrumentation |
| `di/` | Dependency injection container |

All modules are Python packages (used by the backend) with TypeScript
mirrors where needed (event-bus, logger — used by the frontend).
