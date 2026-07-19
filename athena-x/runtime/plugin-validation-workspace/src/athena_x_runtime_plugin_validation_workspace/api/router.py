"""FastAPI router for the Plugin Validation Workspace.

Endpoints:
  GET  /validation/inventory                     → complete component inventory
  GET  /validation/inventory/summary             → inventory summary
  GET  /validation/agents                        → list runtime agents
  GET  /validation/agents/{agent_id}             → one agent's metadata
  POST /validation/agents/{agent_id}/execute     → execute one agent standalone
  POST /validation/agents/{agent_id}/validate    → validate one agent (scenarios + crossval)
  POST /validation/validate-all                  → validate all agents
  GET  /validation/certification                 → Phase 9 certification table
  GET  /validation/summary                       → validation summary
  GET  /validation/health                        → health check
  POST /validation/pipeline                      → execute complete pipeline
"""
from __future__ import annotations
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from athena_x_runtime_logger import get_logger
from ..workspace import PluginValidationWorkspace
from ..logic.scenarios import _bullish_trend_bars, _bars_from_closes

log = get_logger("plugin-validation.api")

router = APIRouter(prefix="/validation", tags=["plugin-validation-workspace"])

_workspace: PluginValidationWorkspace | None = None


def _get_workspace() -> PluginValidationWorkspace:
    global _workspace
    if _workspace is None:
        _workspace = PluginValidationWorkspace()
        _workspace.discover()
    return _workspace


class ExecuteRequest(BaseModel):
    bar_count: int = 60
    closes: list[float] | None = None  # optional: custom close prices


class PipelineRequest(BaseModel):
    bar_count: int = 60


@router.get("/health")
async def health() -> dict:
    try:
        ws = _get_workspace()
        return {
            "status": "ok",
            "components_discovered": ws.get_inventory().to_dict()["summary"],
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.get("/inventory")
async def get_inventory() -> dict:
    """Phase 1 — complete component inventory."""
    ws = _get_workspace()
    return ws.get_inventory_dict()


@router.get("/inventory/summary")
async def get_inventory_summary() -> dict:
    ws = _get_workspace()
    return ws.get_inventory_dict()["summary"]


@router.get("/agents")
async def list_agents() -> dict:
    """List all runtime agents available for validation."""
    ws = _get_workspace()
    agents = [
        {
            "agent_id": a.agent_id,
            "name": a.class_name,
            "layer": a.layer,
            "category": a.category,
            "description": a.description[:200] if a.description else "",
            "module_path": a.module_path,
            "inputs": list(a.inputs),
            "outputs": list(a.outputs),
            "dependencies": list(a.dependencies),
        }
        for a in ws.get_inventory().runtime_agents
    ]
    return {"agents": agents, "total": len(agents)}


@router.get("/agents/{agent_id}")
async def get_agent(agent_id: str) -> dict:
    ws = _get_workspace()
    agent = next(
        (a for a in ws.get_inventory().runtime_agents if a.agent_id == agent_id),
        None
    )
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")
    return {
        "agent_id": agent.agent_id,
        "name": agent.class_name,
        "layer": agent.layer,
        "category": agent.category,
        "description": agent.description,
        "module_path": agent.module_path,
        "file_path": agent.file_path,
        "inputs": list(agent.inputs),
        "outputs": list(agent.outputs),
        "dependencies": list(agent.dependencies),
        "compute_signature": agent.compute_signature,
    }


@router.post("/agents/{agent_id}/execute")
async def execute_agent(agent_id: str, req: ExecuteRequest) -> dict:
    """Phase 3 — execute one agent standalone with raw pipeline view."""
    ws = _get_workspace()
    # Generate bars
    if req.closes:
        bars = _bars_from_closes(req.closes)
    else:
        bars = _bullish_trend_bars(req.bar_count)
    try:
        result = await ws.execute_agent_raw(agent_id, bars=bars)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        log.error("execute_failed", agent_id=agent_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")


@router.post("/agents/{agent_id}/validate")
async def validate_agent(agent_id: str) -> dict:
    """Phase 5+6+8 — validate one agent (scenarios + cross-validation + evidence)."""
    ws = _get_workspace()
    try:
        evidence = await ws.validate_agent(agent_id)
        return evidence.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        log.error("validate_failed", agent_id=agent_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")


@router.post("/validate-all")
async def validate_all() -> dict:
    """Phase 5+6+8 — validate all agents. May take a few seconds."""
    ws = _get_workspace()
    evidence = await ws.validate_all()
    return {
        "evidence": {k: v.to_dict() for k, v in evidence.items()},
        "total": len(evidence),
        "summary": ws.get_summary(),
    }


@router.get("/certification")
async def get_certification() -> dict:
    """Phase 9 — final certification table."""
    ws = _get_workspace()
    return {
        "certification_table": ws.get_certification_table(),
        "summary": ws.get_summary(),
    }


@router.get("/summary")
async def get_summary() -> dict:
    ws = _get_workspace()
    return ws.get_summary()


@router.post("/pipeline")
async def execute_pipeline(req: PipelineRequest) -> dict:
    """Phase 4 — execute complete pipeline."""
    ws = _get_workspace()
    bars = _bullish_trend_bars(req.bar_count)
    result = await ws.execute_complete_pipeline(bars=bars)
    return result
