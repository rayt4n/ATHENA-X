"""Stage 16.5 — Plugin Validation Workspace server.

Standalone uvicorn server that mounts the validation router.
"""
from __future__ import annotations
import sys
sys.path.insert(0, '/home/z/my-project/athena-x/runtime/plugin-validation-workspace/src')

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from athena_x_runtime_plugin_validation_workspace.api.router import router as validation_router


def create_app() -> FastAPI:
    app = FastAPI(title="ATHENA-X Stage 16.5 Plugin Validation Workspace", version="0.1.0")
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
    @app.get("/")
    async def root():
        return {
            "service": "ATHENA-X Stage 16.5 Plugin Validation Workspace",
            "endpoints": [
                "GET  /validation/health",
                "GET  /validation/inventory",
                "GET  /validation/agents",
                "GET  /validation/agents/{id}",
                "POST /validation/agents/{id}/execute",
                "POST /validation/agents/{id}/validate",
                "POST /validation/validate-all",
                "GET  /validation/certification",
                "GET  /validation/summary",
                "POST /validation/pipeline",
            ],
        }
    app.include_router(validation_router)
    return app


app = create_app()

if __name__ == "__main__":
    print("[Stage 16.5] Starting Plugin Validation Workspace server on http://localhost:8001")
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
