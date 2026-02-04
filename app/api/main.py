from __future__ import annotations

from fastapi import FastAPI

from app.api.routes import router


def create_app() -> FastAPI:
    app = FastAPI(
        title="PhishShield",
        version="0.1.0",
        description="Defensive email analysis engine with explainable risk scoring.",
    )
    app.include_router(router)
    return app


app = create_app()
