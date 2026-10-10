"""Zero-key demo mode: deterministic fixture items -> newsletter on disk.

`newsletter-machine run --demo` must work with NO credentials and NO network:
it seeds a small labeled DEMO dataset (all URLs under example.com, all text
clearly fixture content), runs the real pipeline with the stub analyst, and
writes the newsletter files. Rerunning is idempotent (upsert, no duplicates).
Demo rows live under niche id "demo" with "demo-" external ids so they never
collide with collected items; point DATABASE_URL at a scratch file to keep
them out of your real DB entirely.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from newsletter_machine.collectors.base import Item as CollectorItem
from newsletter_machine.config import NicheConfig
from newsletter_machine.db.models import Base
from newsletter_machine.db.models import Niche as NicheRow
from newsletter_machine.logging import get_logger
from newsletter_machine.pipeline.build_flow import build_niche_newsletter
from newsletter_machine.pipeline.deliver import deliver_newsletter

log = get_logger("newsletter_machine.demo")

DEMO_NICHE_ID = "demo"

DEMO_NICHE = NicheConfig(
    id=DEMO_NICHE_ID,
    name="Demo niche (fixtures)",
    description="Deterministic demo dataset. All content is labeled fixture text.",
    keywords_include=["demo-widget", "demo launch"],
    keywords_exclude=["crypto"],
    related_terms=["walkthrough"],
    min_score=0.0,
)

# age_hours keeps the demo fresh forever (relative to run time).
DEMO_ROWS: list[dict[str, Any]] = [
    {
        "platform": "blogs",
        "external_id": "demo-blog-1",
        "url": "https://example.com/demo/blog-1",
        "title": "Demo-Widget launch roundup (FIXTURE)",
        "text": (
            'Ann said "the demo-widget cuts setup time in half for fixture teams" '
            "in this walkthrough. More demo launch details follow in the second paragraph here."
        ),
        "author": "Ann Demo",
        "age_hours": 5,
        "metrics": {"views": 1200, "likes": 90, "comments": 12},
    },
    {
        "platform": "blogs",
        "external_id": "demo-blog-2",
        "url": "https://example.com/demo/blog-2",
        "title": "Demo-Widget launch roundup, reposted (FIXTURE)",
        "text": (
            "Ann said the demo-widget cuts setup time in half for fixture teams "
            "in this walkthrough. More demo launch details follow in the second paragraph here."
        ),
        "author": "Repost Bot",
        "age_hours": 6,
        "metrics": {"views": 40, "likes": 2, "comments": 0},
    },
    {
        "platform": "reddit",
        "external_id": "demo-r1",
        "url": "https://example.com/demo/reddit-1",
        "title": "Which demo-widget plan is worth it? (FIXTURE)",
        "text": (
            "Comparing demo-widget plans for a small fixture team. "
            "What did the demo launch change for you?"
        ),
        "author": "fixture_user",
        "age_hours": 3,
        "metrics": {"upvotes": 320, "comments": 41},
    },
    {
        "platform": "x",
        "external_id": "demo-x1",
        "url": "https://example.com/demo/x-1",
        "title": "Demo launch day notes (FIXTURE)",
        "text": (
            "Demo launch day: the demo-widget walkthrough is live "
            "and fixture teams are trying it now."
        ),
        "author": "@demoteam",
        "age_hours": 1,
        "metrics": {"views": 4000, "likes": 150, "shares": 20, "comments": 9},
    },
    {
        "platform": "quora",
        "external_id": "demo-q1",
        "url": "https://example.com/demo/quora-1",
        "title": "How do I start with the demo-widget? (FIXTURE)",
        "text": "New to the demo-widget. Which walkthrough should a fixture beginner read first?",
        "author": "curious",
        "age_hours": 30,
        "metrics": {},
    },
]


async def run_demo(
    settings: Any, date_str: str | None = None, since_hours: int = 720
) -> dict[str, Any]:
    """Seed fixtures, build with the stub analyst, deliver to files. Zero keys, zero network."""
    from newsletter_machine.collectors.runner import ensure_niche_row, upsert_items
    from newsletter_machine.config import load_newsletter
    from newsletter_machine.db.session import get_engine, make_session_factory
    from newsletter_machine.llm.local_stub import StubLLMClient

    day = date_str or datetime.now(UTC).strftime("%Y-%m-%d")
    newsletter_cfg = load_newsletter(settings)
    engine = get_engine(settings.database_url)
    Base.metadata.create_all(bind=engine)
    factory = make_session_factory(engine)
    now = datetime.now(UTC)
    with factory() as session:
        ensure_niche_row(session, DEMO_NICHE)
        items = [
            CollectorItem(
                platform=row["platform"],
                external_id=row["external_id"],
                url=row["url"],
                canonical_url=row["url"],
                author=row["author"],
                title=row["title"],
                text=row["text"],
                published_at=now - timedelta(hours=row["age_hours"]),
                metrics=dict(row["metrics"]),
                language="en",
                raw={"via": "demo-fixture"},
            )
            for row in DEMO_ROWS
        ]
        inserted, skipped = upsert_items(session, items, DEMO_NICHE_ID)
        session.commit()
        log.info("demo_seeded", extra={"ctx_inserted": inserted, "ctx_skipped": skipped})
        built = await build_niche_newsletter(
            session,
            settings,
            DEMO_NICHE,
            newsletter_cfg,
            day,
            StubLLMClient(),
            since_hours=since_hours,
        )
        receipt = await deliver_newsletter(
            session, settings, newsletter_cfg, built["id"], method="file"
        )
        log.info("demo_done", extra={"ctx_newsletter": built["id"]})
        session.commit()
        niche_count = session.query(NicheRow).count()
    return {
        "date": day,
        "niche_id": DEMO_NICHE_ID,
        "inserted": inserted,
        "skipped": skipped,
        "newsletter_id": built["id"],
        "subject": built["subject"],
        "html_path": built["html_path"],
        "md_path": built["md_path"],
        "txt_path": built["txt_path"],
        "delivery": receipt.get("method"),
        "niche_count": niche_count,
    }
