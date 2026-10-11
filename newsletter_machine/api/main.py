"""FastAPI app factory (Phase 6: JSON API + Jinja/HTMX dashboard)."""

from __future__ import annotations

import time
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from newsletter_machine import __version__
from newsletter_machine.api import (
    routes_dashboard,
    routes_feedback,
    routes_newsletters,
    routes_niches,
    routes_runs,
    routes_sources,
)
from newsletter_machine.api.deps import require_token
from newsletter_machine.logging import get_logger, setup_logging

log = get_logger("newsletter_machine.api")

# Rate limiter
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute", "1000/hour"])

# Security headers for production
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    yield


def create_app() -> FastAPI:
    # Disable default docs endpoints - we'll add protected versions
    app = FastAPI(
        title="Newsletter Machine",
        version=__version__,
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
        lifespan=lifespan,
    )

    # Rate limiting
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    @app.middleware("http")
    async def access_log(request: Request, call_next):
        started = time.monotonic()
        response = await call_next(request)
        log.info(
            "http_request",
            extra={
                "ctx_method": request.method,
                "ctx_path": request.url.path,
                "ctx_status": response.status_code,
                "ctx_ms": round((time.monotonic() - started) * 1000, 1),
            },
        )
        return response

    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        response = await call_next(request)
        # Add security headers
        for header, value in SECURITY_HEADERS.items():
            response.headers[header] = value
        # Add CSP header (relaxed for dashboard/docs, strict for API)
        is_dashboard = request.url.path.startswith("/dashboard") or request.url.path == "/"
        is_docs = request.url.path in ("/docs", "/redoc", "/openapi.json")
        
        if is_dashboard:
            # Dashboard needs inline scripts/styles for HTMX and templates
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://unpkg.com; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data:; "
                "font-src 'self'; "
                "connect-src 'self'; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self'"
            )
        elif is_docs:
            # Docs (Swagger/ReDoc) need external resources from jsdelivr and fastapi.tiangolo.com
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "img-src 'self' data: https://fastapi.tiangolo.com; "
                "font-src 'self' https://cdn.jsdelivr.net; "
                "connect-src 'self'; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self'"
            )
        else:
            # API endpoints - stricter CSP
            response.headers["Content-Security-Policy"] = (
                "default-src 'none'; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self'"
            )
        # HSTS for production (only if behind HTTPS)
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok", "version": __version__}

    # Protected docs endpoints
    @app.get("/docs", dependencies=[Depends(require_token)], include_in_schema=False)
    @limiter.limit("10/minute")
    async def swagger_ui(request: Request) -> str:
        return get_swagger_ui_html(openapi_url="/openapi.json", title="Newsletter Machine API")

    @app.get("/redoc", dependencies=[Depends(require_token)], include_in_schema=False)
    @limiter.limit("10/minute")
    async def redoc_ui(request: Request) -> str:
        return get_redoc_html(openapi_url="/openapi.json", title="Newsletter Machine API")

    @app.get("/openapi.json", dependencies=[Depends(require_token)], include_in_schema=False)
    @limiter.limit("10/minute")
    async def openapi_json(request: Request) -> dict:
        return get_openapi(title="Newsletter Machine", version=__version__, routes=app.routes)

    app.include_router(routes_niches.router, tags=["niches"])
    app.include_router(routes_sources.router, tags=["sources"])
    app.include_router(routes_runs.router, tags=["runs"])
    app.include_router(routes_newsletters.router, tags=["newsletters"])
    app.include_router(routes_feedback.router, tags=["feedback"])
    app.include_router(routes_dashboard.router, tags=["dashboard"])
    return app


app = create_app()


def main() -> None:
    """Run the application with uvicorn (for production)."""
    import uvicorn
    uvicorn.run(
        "newsletter_machine.api.main:app",
        host="0.0.0.0",
        port=8000,
        access_log=False,  # Disable uvicorn's default access log (leaks tokens in query params)
    )


if __name__ == "__main__":
    main()
