"""Stage 16.3 — Minimal workspace server for the dashboard demo.

Starts a uvicorn server on port 8000 with the Institutional Workspace
router mounted. This bypasses the full backend (which has heavy deps
that aren't installable in this environment) and gives the dashboard
a working API to talk to.

Usage:
    python3 /home/z/my-project/scripts/stage16_3_workspace_server.py
"""
from __future__ import annotations
import sys
import os

# Ensure all athena_x_* packages are importable
sys.path.insert(0, '/home/z/my-project/athena-x/runtime/institutional-workspace/src')
sys.path.insert(0, '/home/z/my-project/athena-x/runtime/institutional-workspace/tests')

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from athena_x_runtime_institutional_workspace.api.router import router as workspace_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="ATHENA-X Stage 16.3 Workspace Server",
        version="0.1.0",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )

    @app.get("/")
    async def root():
        return {
            "service": "ATHENA-X Stage 16.3 Workspace Server",
            "endpoints": [
                "GET  /workspace/health",
                "GET  /workspace/summary",
                "GET  /workspace/components",
                "GET  /workspace/components/{agent_id}",
                "POST /workspace/execute/{agent_id}",
                "POST /workspace/execute-request",
                "GET  /workspace/history",
                "GET  /workspace/evidence/{request_id}",
            ],
        }

    @app.get("/health/live")
    async def live():
        return {"status": "alive"}

    app.include_router(workspace_router)
    return app


app = create_app()


if __name__ == "__main__":
    print("[Stage 16.3] Starting workspace server on http://localhost:8000")
    print("[Stage 16.3] Dashboard should connect to http://localhost:8000/workspace/*")
    print("[Stage 16.3] Press Ctrl+C to stop")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
