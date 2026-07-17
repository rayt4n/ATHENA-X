# infrastructure/

Local development infrastructure. Production uses managed services (Supabase Cloud,
Redis Cloud, NATS Cloud, Vercel, GPU instance).

## Services

| Service | Port | Purpose |
|---|---|---|
| Postgres | 5432 | Supabase local dev (4 schemas) |
| Redis | 6379 | Event bus + cache |
| NATS | 4222 | Message queue (alternative transport) |
| Kibana | 5601 | Log viewer (optional) |
