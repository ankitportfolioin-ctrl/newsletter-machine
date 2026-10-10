"""Daily scheduler (APScheduler cron): collect -> build -> deliver per niche.

`newsletter-machine schedule` runs this forever; the same `run_daily()` entry
point works under cron/systemd (`newsletter-machine run` in Phase 7 will also
call it). One niche's failure never stops the others — errors are collected
and reported.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from newsletter_machine.logging import get_logger

log = get_logger("newsletter_machine.scheduler")


def _timezone(name: str):
    try:
        return ZoneInfo(name or "UTC")
    except (ZoneInfoNotFoundError, ValueError):
        return ZoneInfo("UTC")


def run_daily(
    settings: Any | None = None,
    date_str: str | None = None,
    since_hours: int = 24,
    niche_id: str | None = None,
) -> dict[str, Any]:
    """Collect, build and deliver every niche (or one). Returns per-niche outcomes."""
    from newsletter_machine.config import get_settings, load_newsletter, load_niches
    from newsletter_machine.db.models import Base
    from newsletter_machine.db.session import get_engine, make_session_factory
    from newsletter_machine.llm.factory import get_llm_client
    from newsletter_machine.pipeline.build_flow import build_niche_newsletter
    from newsletter_machine.pipeline.deliver import DeliveryError, deliver_newsletter

    settings = settings or get_settings()
    niches = load_niches(settings)
    if niche_id:
        niches = [n for n in niches if n.id == niche_id]
        if not niches:
            raise ValueError(f"unknown niche {niche_id!r}")
    newsletter_cfg = load_newsletter(settings)
    day = date_str or datetime.now(UTC).strftime("%Y-%m-%d")
    engine = get_engine(settings.database_url)
    Base.metadata.create_all(bind=engine)
    factory = make_session_factory(engine)
    client = get_llm_client(settings)

    from newsletter_machine.collectors.runner import collect_and_store

    outcomes: dict[str, Any] = {"date": day, "niches": {}}
    with factory() as session:
        for niche_cfg in niches:
            entry: dict[str, Any] = {}
            try:
                entry["collect"] = asyncio.run(
                    collect_and_store(
                        settings,
                        datetime.now(UTC) - timedelta(hours=since_hours),
                        niche_id=niche_cfg.id,
                    )
                )
            except Exception as e:  # noqa: BLE001 - one niche never stops the day
                entry["collect_error"] = f"{type(e).__name__}: {e}"
                outcomes["niches"][niche_cfg.id] = entry
                continue
            try:
                built = asyncio.run(
                    build_niche_newsletter(
                        session,
                        settings,
                        niche_cfg,
                        newsletter_cfg,
                        day,
                        client,
                        since_hours=max(since_hours, 24),
                    )
                )
                entry["newsletter_id"] = built["id"]
                entry["subject"] = built["subject"]
            except Exception as e:  # noqa: BLE001
                entry["build_error"] = f"{type(e).__name__}: {e}"
                outcomes["niches"][niche_cfg.id] = entry
                continue
            try:
                entry["delivery"] = asyncio.run(
                    deliver_newsletter(session, settings, newsletter_cfg, built["id"])
                )
            except DeliveryError as e:
                entry["delivery_error"] = str(e)
            outcomes["niches"][niche_cfg.id] = entry
            log.info(
                "daily_niche_done",
                extra={
                    "ctx_niche": niche_cfg.id,
                    "ctx_outcome": {k: (v if k != "collect" else "ok") for k, v in entry.items()},
                },
            )
    log.info("daily_run_done", extra={"ctx_date": day, "ctx_niches": len(outcomes["niches"])})
    return outcomes


def build_scheduler(settings: Any | None = None, newsletter_cfg: Any | None = None):
    """APScheduler with one cron job at the configured send time."""
    from apscheduler.schedulers.blocking import BlockingScheduler
    from apscheduler.triggers.cron import CronTrigger

    from newsletter_machine.config import get_settings, load_newsletter

    settings = settings or get_settings()
    newsletter_cfg = newsletter_cfg or load_newsletter(settings)
    hour, minute = 7, 0
    try:
        hour_str, minute_str = str(newsletter_cfg.send_time).split(":")[:2]
        hour, minute = int(hour_str), int(minute_str)
    except ValueError:
        pass
    scheduler = BlockingScheduler(timezone=str(newsletter_cfg.timezone or "UTC"))
    scheduler.add_job(
        lambda: run_daily(settings),
        CronTrigger(hour=hour, minute=minute, timezone=str(newsletter_cfg.timezone or "UTC")),
        id="daily-newsletter",
        replace_existing=True,
    )
    return scheduler
