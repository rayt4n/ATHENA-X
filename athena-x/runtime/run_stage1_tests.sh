#!/usr/bin/env bash
# Run all Stage 1 (Core Foundation) tests.
set -euo pipefail

echo "=== ATHENA-X Stage 1 (Core Foundation) Tests ==="
echo

# 1. Unit tests for each component
for pkg in config logger event-bus health-monitor scheduler di auth secrets; do
    echo "── runtime/$pkg ────────────────────────────────────────"
    cd "runtime/$pkg"
    uv run pytest tests/ -v --tb=short 2>&1 | tail -20
    echo
    cd - > /dev/null
done

# 2. Integration tests
echo "── runtime/integration ──────────────────────────────"
cd runtime/integration
uv run pytest tests/ -v --tb=short -m "functional or integration" 2>&1 | tail -30
echo

echo "── Stress + Performance tests ────────────────────────"
uv run pytest tests/ -v --tb=short -m "stress or performance or failover" 2>&1 | tail -30
echo

echo "=== All Stage 1 tests complete ==="
