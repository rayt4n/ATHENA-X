#!/usr/bin/env bash
set -euo pipefail

echo "=== ATHENA-X Deploy ==="

# 1. Typecheck + lint + test
echo "[1/4] Typecheck + lint + test..."
pnpm typecheck
pnpm lint
pnpm test

# 2. Build frontend
echo "[2/4] Building frontend..."
pnpm --filter @athena-x/dashboard build

# 3. Build backend image
echo "[3/4] Building backend image..."
docker build -t athena-x-backend:latest apps/python-backend/

# 4. Push to registry (skipped in dev)
echo "[4/4] Deploy step — configure your registry in CI"
