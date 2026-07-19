"""Stage 16.5 — Run full validation and save evidence to JSON for PDF report."""
from __future__ import annotations
import asyncio
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, '/home/z/my-project/athena-x/runtime/plugin-validation-workspace/src')

from athena_x_runtime_plugin_validation_workspace import PluginValidationWorkspace

OUT_JSON = Path('/home/z/my-project/scripts/stage16_5_evidence.json')


async def main():
    print("[Stage 16.5] Starting full validation…")
    t0 = time.perf_counter()
    ws = PluginValidationWorkspace()
    inv = ws.discover()
    print(f"  Discovery: {inv.to_dict()['summary']}")

    print("[Stage 16.5] Validating all agents…")
    evidence = await ws.validate_all()
    print(f"  Validated {len(evidence)} agents")

    cert_table = ws.get_certification_table()
    summary = ws.get_summary()
    print(f"  Summary: {summary}")

    payload = {
        "stage": "16.5",
        "generated_at_unix": int(time.time()),
        "duration_seconds": time.perf_counter() - t0,
        "inventory": inv.to_dict(),
        "evidence": {k: v.to_dict() for k, v in evidence.items()},
        "certification_table": cert_table,
        "summary": summary,
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_JSON, 'w') as f:
        json.dump(payload, f, indent=2, default=str)
    print(f"\n[Stage 16.5] Evidence written to {OUT_JSON}")
    print(f"  Certification: {summary['certification_counts']}")


if __name__ == "__main__":
    asyncio.run(main())
