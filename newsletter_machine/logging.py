"""Structured logging (stdlib only, no new dependencies).

JSON lines when demanding machine-readable logs (LOG_FORMAT=json, the
scheduler/docker default) or human-readable lines locally (LOG_FORMAT=text).
Usage: `logger = get_logger(__name__); logger.info("collect_done", extra={...})`.
Never log secrets — callers pass counts/ids/tiers, never tokens or keys.
"""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import UTC, datetime


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict = {
            "ts": datetime.now(UTC).isoformat(),
            "level": record.levelname.lower(),
            "logger": record.name,
            "msg": record.getMessage(),
        }
        extra = {k: v for k, v in record.__dict__.items() if k.startswith("ctx_")}
        if extra:
            payload["ctx"] = {k[4:]: v for k, v in extra.items()}
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


_configured = False


def setup_logging(level: str | None = None, json_format: bool | None = None) -> None:
    """Idempotent root setup. Env: LOG_LEVEL (default INFO), LOG_FORMAT=json|text."""
    global _configured  # noqa: PLW0603 - process-wide logging config by design
    if _configured:
        return
    resolved_level = (level or os.getenv("LOG_LEVEL", "INFO")).upper()
    use_json = json_format if json_format is not None else os.getenv("LOG_FORMAT", "text") == "json"
    handler = logging.StreamHandler(sys.stderr)
    if use_json:
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(getattr(logging, resolved_level, logging.INFO))
    for noisy in ("httpx", "httpcore", "apscheduler", "trafilatura"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
    _configured = True


def get_logger(name: str) -> logging.Logger:
    setup_logging()
    return logging.getLogger(name)


def reset_logging() -> None:  # tests only
    global _configured  # noqa: PLW0603
    _configured = False
    logging.getLogger().handlers.clear()
