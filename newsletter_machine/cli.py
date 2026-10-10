"""Typer CLI: init, doctor, collect, build, send, run, serve, schedule."""

from __future__ import annotations

import os
import shutil
import sys
from datetime import UTC
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from newsletter_machine import __version__
from newsletter_machine.config import clear_config_cache, get_settings, load_niches, load_sources
from newsletter_machine.logging import get_logger, setup_logging

app = typer.Typer(
    name="newsletter-machine", help="Collect, rank, analyze and deliver niche newsletters."
)
console = Console()
log = get_logger("newsletter_machine.cli")


@app.callback()
def _startup(
    log_format: str = typer.Option("", "--log-format", help="text | json (or LOG_FORMAT env)"),
    log_level: str = typer.Option(
        "", "--log-level", help="DEBUG|INFO|WARNING|ERROR (or LOG_LEVEL env)"
    ),
) -> None:
    """Process-wide options: structured logging setup (JSON safe for secrets — counts only)."""
    setup_logging(
        level=log_level or None,
        json_format={"json": True, "text": False}.get(log_format.lower()) if log_format else None,
    )


def _fail(msg: str) -> None:
    console.print(f"[red]{msg}[/red]")


@app.command()
def init(
    force: bool = typer.Option(False, "--force", help="Overwrite existing .env / DB."),
) -> None:
    """Initialize .env from .env.example and create the SQLite database."""
    cwd = Path.cwd()
    example = cwd / ".env.example"
    target = cwd / ".env"
    if target.exists() and not force:
        console.print(f".env already exists at {target} (use --force to overwrite).")
    elif example.exists():
        shutil.copy(example, target)
        console.print(f"Created {target} from .env.example. Edit it with your keys.")
    else:
        _fail("No .env.example found; cannot init .env.")
        raise typer.Exit(code=1)

    from newsletter_machine.db.session import init_db

    settings = get_settings()
    init_db(settings.database_url)
    console.print(f"Database ready: {settings.database_url}")

    # Sync niches from YAML into DB (idempotent upsert)
    try:
        from newsletter_machine.db.models import Niche
        from newsletter_machine.db.session import get_engine, make_session_factory

        niches = load_niches(settings)
        engine = get_engine(settings.database_url)
        factory = make_session_factory(engine)
        with factory() as session:
            for n in niches:
                existing = session.get(Niche, n.id)
                payload = n.model_dump()
                if existing is None:
                    session.add(
                        Niche(
                            id=n.id,
                            name=n.name,
                            description=n.description,
                            config_json=payload,
                        )
                    )
                else:
                    existing.name = n.name
                    existing.description = n.description
                    existing.config_json = payload
            session.commit()
        console.print(f"Synced {len(niches)} niche(s) into the database.")
    except FileNotFoundError as e:
        _fail(str(e))
        raise typer.Exit(code=1) from e


@app.command()
def doctor() -> None:
    """Check env vars, DB, config files, and each collector's tier availability."""
    from sqlalchemy import text

    from newsletter_machine.collectors.registry import available_collectors
    from newsletter_machine.db.session import get_engine

    settings = get_settings()
    table = Table(title=f"Newsletter Machine doctor (v{__version__})")
    table.add_column("Check")
    table.add_column("Result")

    # Python
    table.add_row("python", sys.version.split()[0])

    # Config files
    for label, path in [
        ("niches_yaml", settings.niches_yaml),
        ("sources_yaml", settings.sources_yaml),
        ("newsletter_yaml", settings.newsletter_yaml),
    ]:
        p = Path(path) if Path(path).is_absolute() else Path.cwd() / path
        table.add_row(label, f"OK ({p})" if p.exists() else f"MISSING ({p})")

    # Parse configs honestly
    try:
        niches = load_niches(settings)
        table.add_row("niches", f"OK ({len(niches)} niche(s))")
    except Exception as e:  # noqa: BLE001
        table.add_row("niches", f"ERROR: {e}")

    try:
        sources = load_sources(settings)
        table.add_row("sources", f"OK ({len(sources.collectors)} collector(s) configured)")
    except Exception as e:  # noqa: BLE001
        sources = None  # type: ignore[assignment]
        table.add_row("sources", f"ERROR: {e}")

    # DB
    try:
        engine = get_engine(settings.database_url)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        table.add_row("database", f"OK ({settings.database_url})")
    except Exception as e:  # noqa: BLE001
        table.add_row("database", f"ERROR: {e}")

    # Collectors
    collectors = available_collectors()
    for name in sorted(collectors):
        try:
            tier, note = collectors[name]().tier_status()
            cfg_tier = ""
            if sources is not None and name in sources.collectors:
                cfg = sources.collectors[name]
                cfg_tier = f"config tier={cfg.tier}, enabled={cfg.enabled}"
            table.add_row(f"collector:{name}", f"{tier} — {note} {cfg_tier}".strip())
        except Exception as e:  # noqa: BLE001
            table.add_row(f"collector:{name}", f"ERROR: {e}")

    # Env secrets (presence only, never values)
    for var in [
        "YOUTUBE_API_KEY",
        "REDDIT_CLIENT_ID",
        "X_BEARER_TOKEN",
        "LINKEDIN_ACCESS_TOKEN",
        "INSTAGRAM_ACCESS_TOKEN",
        "ANTHROPIC_API_KEY",
        "OPENAI_API_KEY",
        "PROVIDER_API_KEY",
        "DATABASE_URL",
        "API_TOKEN",
    ]:
        present = bool(os.getenv(var))
        # pydantic-settings maps lowercase field names; also accept those
        table.add_row(f"env:{var}", "set" if present else "not set")

    console.print(table)


@app.command()
def collect(
    niche: str = typer.Option("", "--niche", help="Niche id (default: all niches)"),
    since_hours: int = typer.Option(48, "--since-hours", help="Look back this many hours"),
    limit: int = typer.Option(0, "--limit", help="Per-collector item cap override (0 = config)"),
    platforms: str = typer.Option(
        "", "--platforms", help="Comma-separated subset, e.g. blogs,reddit"
    ),
    manual_file: str = typer.Option(
        "", "--manual-file", help="CSV/JSON/TXT to import as manual items"
    ),
    manual_platform: str = typer.Option(
        "manual", "--manual-platform", help="Platform label for URL-list imports"
    ),
) -> None:
    """Collect items for a niche (or all) and store them idempotently."""
    import asyncio
    from datetime import datetime, timedelta

    from newsletter_machine.config import get_settings

    settings = get_settings()
    plat_list = [p.strip().lower() for p in platforms.split(",") if p.strip()] or None
    manual_items = None
    if manual_file:
        try:
            from newsletter_machine.collectors.manual_import import load_manual_items

            manual_items = load_manual_items(manual_file, manual_platform)
            console.print(f"Loaded {len(manual_items)} manual item(s) from {manual_file}.")
        except (FileNotFoundError, ValueError) as e:
            _fail(str(e))
            raise typer.Exit(code=1) from e
    since = datetime.now(UTC) - timedelta(hours=since_hours)

    from newsletter_machine.collectors.runner import collect_and_store

    try:
        summary = asyncio.run(
            collect_and_store(
                settings,
                since,
                niche_id=niche or None,
                platforms=plat_list,
                limit_override=limit or None,
                manual_items=manual_items,
                manual_niche_id=niche or None,
            )
        )
    except (FileNotFoundError, ValueError) as e:
        _fail(str(e))
        raise typer.Exit(code=1) from e

    table = Table(title="collect results")
    table.add_column("niche / run")
    table.add_column("collector")
    table.add_column("tier")
    table.add_column("items")
    table.add_column("quota")
    table.add_column("errors")
    for run in summary["runs"]:
        for name, stats in run["stats"].items():
            errs = stats["errors"]
            table.add_row(
                f"{run['niche_id']} (run {run['run_id']})",
                name,
                str(stats.get("tier_used", "")),
                str(stats.get("items", 0)),
                str(stats.get("quota_used", 0)),
                "; ".join(errs[:2]) if errs else "",
            )
        table.add_row(
            f"{run['niche_id']} [{run['status']}]",
            "TOTAL",
            "",
            f"+{run['inserted']} new / {run['skipped']} dup",
            "",
            "",
        )
    console.print(table)
    console.print(f"Inserted {summary['inserted']} new, skipped {summary['skipped']} duplicates.")


@app.command()
def build(
    niche: str = typer.Option("", "--niche", help="Niche id (default: all niches)"),
    date: str = typer.Option("", "--date", help="YYYY-MM-DD (default: today UTC)"),
    since_hours: int = typer.Option(168, "--since-hours", help="Item window to analyze"),
    limit: int = typer.Option(50, "--limit", help="Max items per niche into the pipeline"),
    llm: str = typer.Option("", "--llm", help="stub | anthropic | openai (default: settings)"),
    digest: bool = typer.Option(False, "--digest", help="Also build the combined digest"),
) -> None:
    """Analyze ranked items and render the newsletter (HTML/MD/TXT) to disk."""
    import asyncio
    from datetime import UTC, datetime

    from newsletter_machine.config import get_settings, load_newsletter, load_niches

    settings = get_settings()
    date_str = date or datetime.now(UTC).strftime("%Y-%m-%d")
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        _fail(f"bad --date {date_str!r}, want YYYY-MM-DD")
        raise typer.Exit(code=1) from None
    try:
        niches = load_niches(settings)
    except FileNotFoundError as e:
        _fail(str(e))
        raise typer.Exit(code=1) from e
    if niche:
        niches = [n for n in niches if n.id == niche]
        if not niches:
            _fail(f"unknown niche {niche!r}")
            raise typer.Exit(code=1)
    newsletter_cfg = load_newsletter(settings)

    from newsletter_machine.db.models import Base
    from newsletter_machine.db.session import get_engine, make_session_factory
    from newsletter_machine.llm.factory import get_llm_client
    from newsletter_machine.pipeline.build_flow import build_niche_newsletter

    try:
        client = get_llm_client(settings, override=llm or None)
    except Exception as e:  # noqa: BLE001 - clear message for missing keys
        _fail(str(e))
        raise typer.Exit(code=1) from e

    engine = get_engine(settings.database_url)
    Base.metadata.create_all(bind=engine)
    factory = make_session_factory(engine)

    built: list[dict] = []
    with factory() as session:
        for niche_cfg in niches:
            try:
                result = asyncio.run(
                    build_niche_newsletter(
                        session,
                        settings,
                        niche_cfg,
                        newsletter_cfg,
                        date_str,
                        client,
                        since_hours=since_hours,
                        limit=limit,
                    )
                )
            except Exception as e:  # noqa: BLE001 - analysis failure is fatal for build
                _fail(f"build failed for {niche_cfg.id}: {e}")
                raise typer.Exit(code=1) from e
            built.append(result)
            console.print(f"[{niche_cfg.id}] {result['subject']}\n  {result['html_path']}")
        if digest and len(built) > 1:
            from newsletter_machine.db.models import Newsletter as NewsletterRow
            from newsletter_machine.llm.schemas import AnalysisResult as AnalysisResultModel
            from newsletter_machine.pipeline.compose import (
                compose_content,
                compose_digest,
                persist_rendered,
                resolve_db_ids,
            )

            contents = []
            for entry in built:
                row = (
                    session.query(NewsletterRow)
                    .filter_by(date=date_str, niche_id=entry["niche_id"])
                    .one()
                )
                stored = AnalysisResultModel.model_validate(row.content_json["analysis"])
                niche_cfg = next(n for n in niches if n.id == entry["niche_id"])
                story_keys = [
                    s["item_key"]
                    for story in row.content_json["analysis"].get("top_stories", [])
                    for s in story.get("sources", [])
                ]
                contents.append(
                    compose_content(
                        niche_cfg,
                        date_str,
                        stored,
                        {},
                        resolve_db_ids(session, story_keys),
                        row.id,
                        newsletter_cfg,
                    )
                )
            digest_content = compose_digest(contents, date_str, newsletter_cfg)
            digest_result = persist_rendered(
                session,
                settings,
                "digest",
                date_str,
                digest_content.subject,
                digest_content,
                {"digests": [b["niche_id"] for b in built]},
            )
            console.print(f"[digest] {digest_result['subject']}\n  {digest_result['html_path']}")
    console.print(f"Built {len(built)} newsletter(s) for {date_str}.")


@app.command()
def send(
    newsletter: int = typer.Option(..., "--newsletter", help="Newsletter ID"),
    method: str = typer.Option("", "--method", help="file | smtp | resend | webhook | none"),
    to: str = typer.Option("", "--to", help="Comma-separated recipients (overrides config)"),
) -> None:
    """Deliver a built newsletter."""
    import asyncio

    from newsletter_machine.config import get_settings, load_newsletter
    from newsletter_machine.db.models import Base
    from newsletter_machine.db.session import get_engine, make_session_factory
    from newsletter_machine.pipeline.deliver import DeliveryError, deliver_newsletter

    settings = get_settings()
    newsletter_cfg = load_newsletter(settings)
    engine = get_engine(settings.database_url)
    Base.metadata.create_all(bind=engine)
    factory = make_session_factory(engine)
    with factory() as session:
        try:
            receipt = asyncio.run(
                deliver_newsletter(
                    session,
                    settings,
                    newsletter_cfg,
                    newsletter,
                    method=method or None,
                    to_override=[t.strip() for t in to.split(",") if t.strip()] or None,
                )
            )
        except DeliveryError as e:
            _fail(str(e))
            raise typer.Exit(code=1) from e
    console.print(f"Delivered newsletter {newsletter} via {receipt.get('method')}.")


@app.command()
def run(
    niche: str = typer.Option("", "--niche", help="Niche id (default: all niches)"),
    demo: bool = typer.Option(False, "--demo", help="Zero-key fixture demo (no network)"),
    date: str = typer.Option("", "--date", help="YYYY-MM-DD (default: today UTC)"),
    since_hours: int = typer.Option(24, "--since-hours", help="Collection window for full runs"),
) -> None:
    """Full pipeline: collect -> build -> deliver (or deterministic --demo)."""
    import asyncio
    from datetime import UTC, datetime

    from newsletter_machine.config import get_settings

    settings = get_settings()
    date_str = date or datetime.now(UTC).strftime("%Y-%m-%d")
    if demo:
        from newsletter_machine.demo import run_demo

        outcome = asyncio.run(run_demo(settings, date_str))
        table = Table(title=f"demo run ({date_str}) — fixtures only, no network")
        table.add_column("Key")
        table.add_column("Value")
        for key in (
            "niche_id",
            "inserted",
            "skipped",
            "newsletter_id",
            "subject",
            "html_path",
            "md_path",
            "txt_path",
            "delivery",
        ):
            table.add_row(key, str(outcome[key]))
        console.print(table)
        log.info("run_demo_done", extra={"ctx_newsletter": outcome["newsletter_id"]})
        return
    from newsletter_machine.scheduler import run_daily

    try:
        outcomes = run_daily(settings, date_str, since_hours=since_hours, niche_id=niche or None)
    except ValueError as e:
        _fail(str(e))
        raise typer.Exit(code=1) from e
    table = Table(title=f"daily run ({outcomes['date']})")
    table.add_column("niche")
    table.add_column("collect")
    table.add_column("newsletter")
    table.add_column("delivery")
    for niche_id, entry in outcomes["niches"].items():
        collect = entry.get("collect_error") or (
            f"+{entry.get('collect', {}).get('inserted', 0)} new"
            if isinstance(entry.get("collect"), dict)
            else "ok"
        )
        table.add_row(
            niche_id,
            str(collect),
            str(entry.get("subject") or entry.get("build_error", "—")),
            str((entry.get("delivery") or {}).get("method", entry.get("delivery_error", "—"))),
        )
    console.print(table)


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", "--host"),
    port: int = typer.Option(8000, "--port"),
) -> None:
    """Serve the API + dashboard."""
    import uvicorn

    console.print(f"Serving on http://{host}:{port} (dashboard at /dashboard?token=...)")
    uvicorn.run("newsletter_machine.api.main:app", host=host, port=port)


@app.command()
def schedule() -> None:
    """Run the daily scheduler (blocking; Ctrl-C to stop)."""
    from newsletter_machine.config import get_settings, load_newsletter
    from newsletter_machine.scheduler import build_scheduler

    settings = get_settings()
    newsletter_cfg = load_newsletter(settings)
    scheduler = build_scheduler(settings, newsletter_cfg)
    jobs = scheduler.get_jobs()
    console.print(
        f"Scheduled {len(jobs)} job(s); next run at {jobs[0].next_run_time} "
        f"({newsletter_cfg.send_time} {newsletter_cfg.timezone}). Press Ctrl-C to stop."
    )
    try:
        scheduler.start()
    except KeyboardInterrupt:
        console.print("Scheduler stopped.")


if __name__ == "__main__":  # pragma: no cover
    clear_config_cache()
    app()
