"""Collection orchestration: run enabled collectors, upsert idempotently, log Runs.

Contract: a platform failure degrades the newsletter gracefully — per-collector
errors are recorded on the Run row, never raised.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from newsletter_machine.collectors.base import CollectorResult, Item
from newsletter_machine.collectors.registry import available_collectors
from newsletter_machine.config import Settings, load_niches, load_sources
from newsletter_machine.db.models import Item as ItemRow
from newsletter_machine.db.models import Niche as NicheRow
from newsletter_machine.db.models import Run as RunRow
from newsletter_machine.logging import get_logger
from newsletter_machine.pipeline.normalize import canonicalize_url

log = get_logger("newsletter_machine.collect")


def build_collector(name: str, cfg: Any, settings: Settings):  # noqa: ANN401, ARG001
    """Construct a collector, applying rate limits + preferred tier from sources.yaml."""
    from newsletter_machine.collectors.blogs import BlogsCollector
    from newsletter_machine.collectors.instagram import InstagramCollector
    from newsletter_machine.collectors.linkedin import LinkedInCollector
    from newsletter_machine.collectors.quora import QuoraCollector
    from newsletter_machine.collectors.reddit import RedditCollector
    from newsletter_machine.collectors.x_twitter import XTwitterCollector
    from newsletter_machine.collectors.youtube import YouTubeCollector

    per_min = getattr(cfg, "rate_limit_per_min", 30) if cfg else 30
    tier = getattr(cfg, "tier", None) if cfg else None
    if name == "blogs":
        return BlogsCollector(per_min=per_min)
    if name == "youtube":
        return YouTubeCollector(per_min=per_min)
    if name == "reddit":
        return RedditCollector(per_min=per_min)
    if name == "x":
        return XTwitterCollector(per_min=per_min, preferred_tier=tier)
    if name == "linkedin":
        return LinkedInCollector(per_min=per_min, preferred_tier=tier)
    if name == "instagram":
        return InstagramCollector(per_min=per_min, preferred_tier=tier)
    if name == "quora":
        return QuoraCollector(per_min=per_min, preferred_tier=tier)
    klass = available_collectors().get(name)
    if klass is None:
        raise KeyError(f"unknown collector: {name}")
    return klass()


async def run_collectors(
    niche: Any,
    sources: Any,
    settings: Settings,  # noqa: ARG001 - kept for Phase 3 provider wiring
    since: datetime,
    platforms: list[str] | None = None,
    limit_override: int | None = None,
) -> dict[str, CollectorResult]:
    """Run each enabled collector for *niche*. Never raises for platform errors."""
    results: dict[str, CollectorResult] = {}
    allowed = {p.lower() for p in platforms} if platforms else None
    for name in available_collectors():
        cfg = sources.collectors.get(name) if sources else None
        if cfg is not None and not cfg.enabled:
            continue
        if allowed is not None and name not in allowed:
            continue
        limit = limit_override or (cfg.item_cap_per_run if cfg else 50)
        try:
            collector = build_collector(name, cfg, settings)
            results[name] = await collector.collect(niche, since, limit)
        except Exception as e:  # noqa: BLE001 - contract: never crash the run
            results[name] = CollectorResult(
                items=[], errors=[f"{name}: {type(e).__name__}: {e}"], tier_used="disabled"
            )
    return results


def ensure_niche_row(session: Session, niche: Any) -> None:
    existing = session.get(NicheRow, niche.id)
    payload = niche.model_dump() if hasattr(niche, "model_dump") else {}
    if existing is None:
        session.add(
            NicheRow(
                id=niche.id,
                name=niche.name,
                description=niche.description or "",
                config_json=payload,
            )
        )
    else:
        existing.name = niche.name
        existing.description = niche.description or ""
        existing.config_json = payload


def upsert_items(session: Session, items: list[Item], niche_id: str) -> tuple[int, int]:
    """Insert new items, skip existing (platform, external_id). Returns (inserted, skipped)."""
    inserted = 0
    skipped = 0
    for item in items:
        exists = (
            session.query(ItemRow)
            .filter_by(platform=item.platform, external_id=item.external_id)
            .one_or_none()
        )
        if exists is not None:
            skipped += 1
            continue
        session.add(
            ItemRow(
                platform=item.platform,
                external_id=item.external_id,
                url=item.url,
                canonical_url=item.canonical_url or canonicalize_url(item.url),
                author=item.author or "",
                title=item.title or "",
                text=item.text or "",
                media_urls=list(item.media_urls or []),
                published_at=item.published_at,
                metrics_json=dict(item.metrics or {}),
                language=item.language or "en",
                niche_id=niche_id,
                raw_json=dict(item.raw or {}),
            )
        )
        try:
            session.flush()
            inserted += 1
        except IntegrityError:
            session.rollback()
            skipped += 1
    return inserted, skipped


async def collect_and_store(
    settings: Settings,
    since: datetime,
    niche_id: str | None = None,
    platforms: list[str] | None = None,
    limit_override: int | None = None,
    manual_items: list[Item] | None = None,
    manual_niche_id: str | None = None,
) -> dict:
    """Full collect-then-store for one or all niches. Returns a JSON-able summary."""
    from newsletter_machine.db.session import get_engine, make_session_factory

    niches = load_niches(settings)
    if niche_id:
        niches = [n for n in niches if n.id == niche_id]
        if not niches:
            raise ValueError(f"unknown niche {niche_id!r}")
    sources = load_sources(settings)
    engine = get_engine(settings.database_url)
    # Ensure schema exists (fresh clones may not have run init)
    from newsletter_machine.db.models import Base

    Base.metadata.create_all(bind=engine)
    factory = make_session_factory(engine)

    summary_runs: list[dict] = []
    total_inserted = 0
    total_skipped = 0
    with factory() as session:
        for niche in niches:
            run = RunRow(niche_id=niche.id, status="started", stats_json={}, errors_json=[])
            session.add(run)
            session.flush()
            ensure_niche_row(session, niche)
            results = await run_collectors(
                niche, sources, settings, since, platforms, limit_override
            )
            stats: dict[str, dict] = {}
            flat_errors: list[str] = []
            inserted = 0
            skipped = 0
            for name, res in results.items():
                stats[name] = {
                    "items": len(res.items),
                    "errors": res.errors,
                    "quota_used": res.quota_used,
                    "tier_used": res.tier_used,
                }
                flat_errors.extend(f"{name}: {e}" for e in res.errors)
                ins, skp = upsert_items(session, res.items, niche.id)
                inserted += ins
                skipped += skp
            if manual_items and (manual_niche_id is None or manual_niche_id == niche.id):
                ins, skp = upsert_items(session, manual_items, niche.id)
                inserted += ins
                skipped += skp
                stats["manual"] = {
                    "items": len(manual_items),
                    "errors": [],
                    "quota_used": 0,
                    "tier_used": "manual",
                }
            failed = [n for n, r in results.items() if r.items == [] and r.errors]
            status = "success" if not flat_errors else ("partial" if inserted else "failed")
            if not results and not manual_items:
                status = "failed"
                flat_errors.append("no collectors ran (all disabled or filtered out)")
            _ = failed
            run.status = status
            run.finished_at = datetime.now(UTC)
            run.stats_json = stats
            run.errors_json = flat_errors
            session.add(run)
            session.commit()
            collector_summary = {
                name: {"items": entry["items"], "tier": entry["tier_used"]}
                for name, entry in stats.items()
            }
            log.info(
                "niche_collected",
                extra={
                    "ctx_niche": niche.id,
                    "ctx_run": run.id,
                    "ctx_status": status,
                    "ctx_inserted": inserted,
                    "ctx_skipped": skipped,
                    "ctx_collectors": collector_summary,
                },
            )
            total_inserted += inserted
            total_skipped += skipped
            summary_runs.append(
                {
                    "run_id": run.id,
                    "niche_id": niche.id,
                    "status": status,
                    "inserted": inserted,
                    "skipped": skipped,
                    "stats": stats,
                }
            )
    return {"runs": summary_runs, "inserted": total_inserted, "skipped": total_skipped}
