#!/usr/bin/env python3
"""Seed the development Supabase instance with default data."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEED_FILE = ROOT / "database" / "seeds" / "dev_symbols.sql"

if not SEED_FILE.exists():
    print(f"Seed file not found: {SEED_FILE}")
    sys.exit(1)

db_url = os.environ.get("DATABASE_URL")
if not db_url:
    print("DATABASE_URL not set")
    sys.exit(1)

subprocess.run(["psql", db_url, "-f", str(SEED_FILE)], check=True)
print("✓ Seed data applied")
