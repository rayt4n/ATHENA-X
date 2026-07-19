"""FastAPI router for the Institutional Workspace.

Endpoints:
  GET  /workspace/components              → list all runtime agents
  GET  /workspace/components/{agent_id}   → one agent's metadata
  GET  /workspace/summary                 → summary stats
  POST /workspace/execute/{agent_id}      → execute one agent standalone
  POST /workspace/execute-request         → execute full Layer 1→5 pipeline
  GET  /workspace/history                 → recent trace history
  GET  /workspace/evidence/{request_id}   → evidence report for a past request
  GET  /workspace/health                  → workspace health check
"""
from __future__ import annotations
from typing import Any
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException

from athena_x_runtime_logger import get_logger
from ..workspace import InstitutionalWorkspace
from athena_x_ta_base import Timeframe

log = get_logger("institutional-workspace.api")

router = APIRouter(prefix="/workspace", tags=["institutional-workspace"])

# Singleton workspace instance — initialized on first request
_workspace: InstitutionalWorkspace | None = None


def _get_workspace() -> InstitutionalWorkspace:
    global _workspace
    if _workspace is None:
        _workspace = InstitutionalWorkspace()
        _workspace.discover()
    return _workspace


class ExecuteRequest(BaseModel):
    symbol: str = "SPY"
    timeframe: str = "15m"
    data_provider: str = "in-memory"


class ExecuteAgentRequest(BaseModel):
    symbol: str = "SPY"
    timeframe: str = "15m"


@router.get("/health")
async def health() -> dict:
    """Health check — confirms workspace is initialized."""
    try:
        ws = _get_workspace()
        return {
            "status": "ok",
            "adapters_registered": ws.get_summary()["total_adapters"],
            "history_size": len(ws._history),
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.get("/summary")
async def summary() -> dict:
    """Get workspace summary stats."""
    ws = _get_workspace()
    return ws.get_summary()


@router.get("/components")
async def list_components() -> dict:
    """List all runtime components."""
    ws = _get_workspace()
    return {
        "components": ws.list_components(),
        "total": ws.get_summary()["total_adapters"],
    }


@router.get("/components/{agent_id}")
async def get_component(agent_id: str) -> dict:
    """Get one component's full metadata."""
    ws = _get_workspace()
    comp = ws.get_component(agent_id)
    if comp is None:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")
    return comp


@router.post("/execute/{agent_id}")
async def execute_agent(agent_id: str, req: ExecuteAgentRequest) -> dict:
    """Execute a single agent standalone."""
    ws = _get_workspace()
    # Build a fake repo for demo purposes (real deployments inject a real repo)
    repo = _build_demo_repo()
    try:
        tf = _parse_timeframe(req.timeframe)
        result = await ws.execute_agent(agent_id, req.symbol, tf, repo)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        log.error("execute_agent_failed", agent_id=agent_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")


@router.post("/execute-request")
async def execute_request(req: ExecuteRequest) -> dict:
    """Execute the full Layer 1→5 pipeline with tracing."""
    ws = _get_workspace()
    repo = _build_demo_repo()
    try:
        tf = _parse_timeframe(req.timeframe)
        result = await ws.execute_request(req.symbol, tf, repo, data_provider=req.data_provider)
        return result
    except Exception as e:
        log.error("execute_request_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")


@router.get("/history")
async def history(limit: int = 50) -> dict:
    """Get recent trace history."""
    ws = _get_workspace()
    return {"history": ws.get_history(limit=limit), "count": len(ws._history)}


@router.get("/evidence/{request_id}")
async def evidence(request_id: str) -> dict:
    """Get the evidence report for a past request."""
    ws = _get_workspace()
    report = ws.get_evidence_report(request_id)
    if report is None:
        raise HTTPException(status_code=404, detail=f"Request not found: {request_id}")
    return report


# ─── Helpers ────────────────────────────────────────────────────────────

def _parse_timeframe(tf_str: str) -> Timeframe:
    """Parse a timeframe string into a Timeframe enum."""
    mapping = {
        "1m": Timeframe.ONE_MIN,
        "5m": Timeframe.FIVE_MIN,
        "15m": Timeframe.FIFTEEN_MIN,
        "30m": Timeframe.THIRTY_MIN,
        "1H": Timeframe.ONE_HOUR,
        "4H": Timeframe.FOUR_HOUR,
        "1D": Timeframe.DAILY,
        "1W": Timeframe.WEEKLY,
        "1M": Timeframe.MONTHLY,
    }
    if tf_str not in mapping:
        raise HTTPException(status_code=400, detail=f"Unknown timeframe: {tf_str}")
    return mapping[tf_str]


def _build_demo_repo():
    """Build a deterministic demo repo (FakeMarketRepository pattern)."""
    from datetime import datetime, timezone, timedelta
    from athena_x_runtime_repository_interface import QueryResult

    class DemoRepo:
        """Deterministic fake repo for dashboard demo purposes."""
        async def query_bars(self, symbol, timeframe, start, end):
            bars = []
            base_price = 450.0 if symbol == "SPY" else 100.0
            base = datetime.now(timezone.utc) - timedelta(days=200)
            for i in range(200):
                ts = base + timedelta(minutes=i * 15)
                price = base_price + i * 0.1 + (i % 7) * 0.5 - (i % 3) * 0.3
                bars.append({
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "timestamp": ts.isoformat(),
                    "open": round(price - 0.2, 4),
                    "high": round(price + 0.5, 4),
                    "low": round(price - 0.5, 4),
                    "close": round(price, 4),
                    "volume": 100000 + i * 100,
                })
            return QueryResult(records=bars, count=len(bars))

        async def read_quote(self, symbol):
            return None

        async def write_quote(self, record):
            pass

        async def write_bar(self, record):
            pass

        async def supersede(self, record_id, corrected):
            pass

        async def get_history(self, symbol, limit=100):
            return QueryResult(records=[], count=0)

    return DemoRepo()
