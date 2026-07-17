#!/usr/bin/env bash
set -euo pipefail

echo "=== ATHENA-X Dev Setup ==="

# 1. Check prerequisites
command -v node >/dev/null || { echo "Node.js required"; exit 1; }
command -v pnpm >/dev/null || { echo "pnpm required"; exit 1; }
command -v python3 >/dev/null || { echo "Python 3.11+ required"; exit 1; }
command -v uv >/dev/null || { echo "uv required (pip install uv)"; exit 1; }
command -v docker >/dev/null || { echo "Docker required"; exit 1; }

# 2. Install workspace deps
echo "[1/5] Installing pnpm workspace..."
pnpm install

echo "[2/5] Installing Python workspace..."
uv sync

# 3. Start infrastructure
echo "[3/5] Starting Docker infrastructure..."
docker compose -f infrastructure/docker-compose.yml up -d

# 4. Apply migrations + seeds
echo "[4/5] Applying database migrations..."
supabase db push || echo "Supabase not configured — skipping migrations"

# 5. Copy env
echo "[5/5] Setting up .env..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env from .env.example — edit with your API keys"
fi

echo ""
echo "✅ Setup complete. Run:"
echo "  cd apps/python-backend && uv run uvicorn athena_x_backend.main:app --reload"
echo "  cd apps/nextjs-dashboard && pnpm dev"
