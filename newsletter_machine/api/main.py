"""FastAPI app factory (Phase 6: JSON API + Jinja/HTMX dashboard)."""

from __future__ import annotations

import time

from fastapi import FastAPI, Request

from newsletter_machine import __version__
from newsletter_machine.api import (
    routes_dashboard,
    routes_feedback,
    routes_newsletters,
    routes_niches,
    routes_runs,
    routes_sources,
)
from newsletter_machine.logging import get_logger, setup_logging

log = get_logger("newsletter_machine.api")


def create_app() -> FastAPI:
    setup_logging()
    app = FastAPI(title="Newsletter Machine", version=__version__)

    @app.middleware("http")
    async def access_log(request: Request, call_next):
        started = time.monotonic()
        response = await call_next(request)
        log.info(
            "http_request",
            extra={
                "ctx_method": request.method, "ctx_path": request.url.path,
                "ctx_status": response.status_code,
                "ctx_ms": round((time.monotonic() - started) * 1000, 1),
            },
        )
        return response

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok", "version": __version__}

    app.include_router(routes_niches.router, tags=["niches"])
    app.include_router(routes_sources.router, tags=["sources"])
    app.include_router(routes_runs.router, tags=["runs"])
    app.include_router(routes_newsletters.router, tags=["newsletters"])
    app.include_router(routes_feedback.router, tags=["feedback"])
    app.include_router(routes_dashboard.router, tags=["dashboard"])
    return app


app = create_app()
