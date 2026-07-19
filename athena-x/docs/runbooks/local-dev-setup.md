# Local Dev Setup

## Prerequisites

- Node.js 20+
- pnpm 9+
- Python 3.11+
- uv (Python package manager)
- Docker (for Redis + NATS + Postgres)
- Supabase CLI

## Steps

```bash
# 1. Clone the repo
git clone <repo-url> athena-x
cd athena-x

# 2. Install workspace deps
pnpm install
uv sync

# 3. Start infrastructure (Postgres + Redis + NATS)
docker compose -f infrastructure/docker-compose.yml up -d

# 4. Apply database migrations
supabase db push

# 5. Seed dev data
psql $DATABASE_URL -f database/seeds/dev_symbols.sql

# 6. Copy env file and fill in API keys
cp .env.example .env
# Edit .env with your provider API keys

# 7. Start the backend
cd apps/python-backend
uv run uvicorn athena_x_backend.main:app --reload --port 8000

# 8. In a new terminal, start the dashboard
cd apps/nextjs-dashboard
pnpm dev
```

Dashboard: http://localhost:3000
Backend: http://localhost:8000/docs (Swagger)
