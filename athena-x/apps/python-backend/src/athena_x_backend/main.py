"""FastAPI app entry point."""
from __future__ import annotations
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup + shutdown lifecycle.

    Stage 16.3: Initializes the Institutional Workspace on startup.
    """
    # Pre-warm the institutional workspace so the first request is fast
    try:
        from athena_x_runtime_institutional_workspace.api.router import _get_workspace
        ws = _get_workspace()
        print(f"[Stage 16.3] Institutional Workspace initialized: {ws.get_summary()}")
    except Exception as e:
        print(f"[Stage 16.3] Workspace init failed (will lazy-init on first request): {e}")
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="ATHENA-X Backend",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:3001"],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )

    @app.get("/health/live")
    async def live():
        return {"status": "alive"}

    @app.get("/health/ready")
    async def ready():
        return {"status": "ready"}

    # Stage 16.3: Mount the Institutional Workspace router
    try:
        from athena_x_runtime_institutional_workspace.api.router import router as workspace_router
        app.include_router(workspace_router)
        print("[Stage 16.3] Institutional Workspace router mounted at /workspace/*")
    except ImportError as e:
        print(f"[Stage 16.3] Workspace router not available: {e}")

    return app


app = create_app()
