"""FastAPI app entry point."""
from __future__ import annotations
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup + shutdown lifecycle.

    STEP 4 will:
    - Connect to event bus
    - Start all agents (data-collection → raw-intelligence → decision-intelligence → supervisor)
    - Start health monitor
    - Start scheduler
    """
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="ATHENA-X Backend",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
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

    return app


app = create_app()
