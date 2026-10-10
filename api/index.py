"""Vercel serverless entrypoint: re-exports the FastAPI app.

Vercel's Python runtime looks for an `app` instance in api/index.py (this
file) and serves the whole application as one function. Local runs still use
`newsletter_machine.api.main:app` via uvicorn — same object, no fork.
"""

from newsletter_machine.api.main import app  # noqa: F401  (re-exported for Vercel)

__all__ = ["app"]
