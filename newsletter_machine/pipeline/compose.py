"""Composer: validated analysis -> newsletter object -> HTML/MD/TXT + files.

Sections follow newsletter.yaml (order + enabled + max_items). Every story
carries its source URLs and a feedback link (thumbs up/down hit the Phase 6
API; until then they are stable relative URLs). The diagnostics footer always
reports sources used, tiers, failures and counts — a degraded run degrades the
footer, never the whole newsletter. Re-running the same day/niche upserts the
Newsletter row and overwrites the files (idempotent).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from newsletter_machine.llm.schemas import AnalysisResult

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"

SECTION_SOURCES = {
    "tldr": "tldr",
    "top_stories": "top_stories",
    "trend_radar": "trends",
    "platform_highlights": "platform_highlights",
    "voices": "quotes",
    "questions": "questions",
    "opportunities": "opportunities",
    "action": "action_today",
    "coverage": "coverage",
}


@dataclass
class StoryView:
    title: str
    summary: str
    why_it_matters: str
    sources: list[dict[str, str]] = field(default_factory=list)
    feedback_up: str = ""
    feedback_down: str = ""


@dataclass
class NewsletterContent:
    niche_id: str
    niche_name: str
    date: str
    subject: str
    preheader: str
    name: str = ""
    tagline: str = ""
    tldr: list[str] = field(default_factory=list)
    top_stories: list[StoryView] = field(default_factory=list)
    trends: list[dict] = field(default_factory=list)
    platform_highlights: list[dict] = field(default_factory=list)
    quotes: list[dict] = field(default_factory=list)
    questions: list[dict] = field(default_factory=list)
    opportunities: list[dict] = field(default_factory=list)
    creator_watch: list[dict] = field(default_factory=list)
    action_today: str = ""
    coverage: dict[str, int] = field(default_factory=dict)
    confidence_note: str = ""
    diagnostics: dict = field(default_factory=dict)
    enabled_sections: list[str] = field(default_factory=list)


def _section_cfg(newsletter_cfg: Any, name: str) -> tuple[bool, int]:
    sections = getattr(newsletter_cfg, "sections", {}) or {}
    cfg = sections.get(name)
    if cfg is None:
        return True, 10**9
    return bool(cfg.enabled), int(cfg.max_items)


def _feedback_link(newsletter_id: Any, item_id: Any, signal: str) -> str:
    if newsletter_id is None or item_id is None:
        return ""
    return f"/feedback?newsletter_id={newsletter_id}&item_id={item_id}&signal={signal}"


def compose_content(
    niche: Any,
    date_str: str,
    analysis: AnalysisResult,
    diagnostics: dict | None = None,
    key_to_db_id: dict[str, int] | None = None,
    newsletter_id: int | None = None,
    newsletter_cfg: Any | None = None,
) -> NewsletterContent:
    """Assemble render-ready content. Pure (no I/O)."""
    key_to_db_id = key_to_db_id or {}
    diagnostics = diagnostics or {}
    niche_id = str(getattr(niche, "id", "digest"))
    niche_name = str(getattr(niche, "name", "Combined digest"))
    subject = str(getattr(newsletter_cfg, "subject_style", "{date} — {niche}: top stories")).format(
        date=date_str, niche=niche_name
    )
    order = list(getattr(newsletter_cfg, "sections_order", []) or list(SECTION_SOURCES))
    enabled_sections = [
        s for s in order if s in SECTION_SOURCES and _section_cfg(newsletter_cfg, s)[0]
    ]

    def cap(name: str, values: list) -> list:
        _, max_items = _section_cfg(newsletter_cfg, name)
        return list(values)[: max(0, max_items)]

    stories: list[StoryView] = []
    for story in cap("top_stories", analysis.top_stories):
        first_key = story.sources[0].item_key if story.sources else ""
        db_id = key_to_db_id.get(first_key)
        stories.append(
            StoryView(
                title=story.title,
                summary=story.summary,
                why_it_matters=story.why_it_matters,
                sources=[
                    {"platform": s.platform, "url": s.url, "key": s.item_key} for s in story.sources
                ],
                feedback_up=_feedback_link(newsletter_id, db_id, "up"),
                feedback_down=_feedback_link(newsletter_id, db_id, "down"),
            )
        )
    preheader = (analysis.tldr[0] if analysis.tldr else f"{niche_name} daily briefing")[:140]
    return NewsletterContent(
        niche_id=niche_id,
        niche_name=niche_name,
        date=date_str,
        subject=subject,
        preheader=preheader,
        name=str(getattr(newsletter_cfg, "name", "Daily Signal")),
        tagline=str(getattr(newsletter_cfg, "tagline", "")),
        tldr=cap("tldr", analysis.tldr),
        top_stories=stories,
        trends=[t.model_dump() for t in cap("trend_radar", analysis.trends)],
        platform_highlights=[
            h.model_dump() for h in cap("platform_highlights", analysis.platform_highlights)
        ],
        quotes=[q.model_dump() for q in cap("voices", analysis.quotes)],
        questions=[q.model_dump() for q in cap("questions", analysis.questions)],
        opportunities=[o.model_dump() for o in cap("opportunities", analysis.opportunities)],
        creator_watch=[c.model_dump() for c in analysis.creator_watch],
        action_today=analysis.action_today if "action" in enabled_sections else "",
        coverage=dict(analysis.coverage),
        confidence_note=analysis.confidence_note,
        diagnostics=diagnostics,
        enabled_sections=enabled_sections,
    )


def compose_digest(
    contents: list[NewsletterContent], date_str: str, newsletter_cfg: Any | None = None
) -> NewsletterContent:
    """Optional combined digest: TL;DR + top stories across niches, same templates."""
    subject = str(getattr(newsletter_cfg, "subject_style", "{date} — {niche}: top stories")).format(
        date=date_str, niche="All niches"
    )
    order = list(getattr(newsletter_cfg, "sections_order", []) or list(SECTION_SOURCES))
    enabled_sections = [
        s for s in order if s in SECTION_SOURCES and _section_cfg(newsletter_cfg, s)[0]
    ]

    def cap(name: str, values: list) -> list:
        _, max_items = _section_cfg(newsletter_cfg, name)
        return list(values)[: max(0, max_items)]

    tldr = [f"[{c.niche_name}] {bullet}" for c in contents for bullet in c.tldr][:5]
    stories = [s for c in contents for s in c.top_stories][:7]
    return NewsletterContent(
        niche_id="digest",
        niche_name="All niches",
        date=date_str,
        subject=subject,
        preheader="Combined digest: " + (tldr[0] if tldr else "today's top stories")[:120],
        name=str(getattr(newsletter_cfg, "name", "Daily Signal")),
        tagline=str(getattr(newsletter_cfg, "tagline", "")),
        tldr=cap("tldr", tldr or ["Light day across all niches."]),
        top_stories=cap("top_stories", stories),
        trends=[],
        platform_highlights=[],
        quotes=[],
        questions=[],
        opportunities=[],
        creator_watch=[],
        action_today="",
        coverage={c.niche_name: len(c.top_stories) for c in contents},
        confidence_note=f"Combined digest of {len(contents)} niche(s).",
        diagnostics={"digests": [c.niche_id for c in contents]},
        enabled_sections=enabled_sections,
    )


def _jinja_env() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=True, undefined=StrictUndefined
    )


def render_html(content: NewsletterContent) -> str:
    html = _jinja_env().get_template("newsletter.html.j2").render(n=content)
    try:
        from premailer import transform

        return transform(html)
    except Exception:
        return html  # email CSS stays in <style>; still renders fine


def render_markdown(content: NewsletterContent) -> str:
    return _jinja_env().get_template("newsletter.md.j2").render(n=content)


def render_text(content: NewsletterContent) -> str:
    return _jinja_env().get_template("newsletter.txt.j2").render(n=content)


def resolve_db_ids(session: Any, keys: list[str]) -> dict[str, int]:
    """Map item keys (platform:external_id) to DB ids. Best-effort, never raises."""
    from newsletter_machine.db.models import Item as ItemRow

    mapping: dict[str, int] = {}
    try:
        for key in keys:
            if ":" not in key:
                continue
            platform, external_id = key.split(":", 1)
            row = (
                session.query(ItemRow)
                .filter_by(platform=platform, external_id=external_id)
                .one_or_none()
            )
            if row is not None:
                mapping[key] = row.id
    except Exception:
        pass
    return mapping


def persist_rendered(
    session: Any,
    settings: Any,
    niche_id: str,
    date_str: str,
    subject: str,
    content: NewsletterContent,
    extra_json: dict | None = None,
) -> dict[str, Any]:
    """Render content to HTML/MD/TXT, write files, upsert the Newsletter row.

    On read-only filesystems (e.g. Vercel serverless) the file writes are
    skipped with a warning and the analysis stays queryable in the DB row —
    the preview endpoint re-renders HTML from it. Nothing raises for I/O.
    """
    from newsletter_machine.db.models import Newsletter as NewsletterRow
    from newsletter_machine.logging import get_logger

    out_dir = Path(settings.output_dir) / date_str / niche_id
    html, markdown, text = render_html(content), render_markdown(content), render_text(content)
    html_path = out_dir / "newsletter.html"
    md_path = out_dir / "newsletter.md"
    txt_path = out_dir / "newsletter.txt"
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
        html_path.write_text(html, encoding="utf-8")
        md_path.write_text(markdown, encoding="utf-8")
        txt_path.write_text(text, encoding="utf-8")
    except OSError as e:
        get_logger("newsletter_machine.compose").warning(
            "file_write_skipped",
            extra={"ctx_dir": str(out_dir), "ctx_error": f"{type(e).__name__}: {e}"},
        )
        html_path = md_path = txt_path = None  # type: ignore[assignment] - recorded as "" below
    row = session.query(NewsletterRow).filter_by(date=date_str, niche_id=niche_id).one_or_none()
    if row is None:
        row = NewsletterRow(date=date_str, niche_id=niche_id, subject=subject, status="built")
        session.add(row)
        session.flush()
    row.subject = subject
    row.html_path = str(html_path) if html_path else ""
    row.md_path = str(md_path) if md_path else ""
    row.txt_path = str(txt_path) if txt_path else ""
    row.content_json = extra_json or {}
    row.status = "built"
    session.add(row)
    session.commit()
    return {
        "id": row.id,
        "subject": subject,
        "html_path": str(html_path) if html_path else "",
        "md_path": str(md_path) if md_path else "",
        "txt_path": str(txt_path) if txt_path else "",
    }


def build_newsletter(
    session: Any,
    settings: Any,
    niche: Any,
    date_str: str,
    analysis: AnalysisResult,
    diagnostics: dict | None = None,
    key_to_db_id: dict[str, int] | None = None,
    newsletter_cfg: Any | None = None,
    niche_label: str | None = None,
) -> dict[str, Any]:
    """Render + write files + upsert Newsletter row. Returns paths + id + subject."""
    from newsletter_machine.db.models import Newsletter as NewsletterRow

    niche_id = niche_label or str(getattr(niche, "id", "digest"))

    # Reserve the row first so feedback links carry the real newsletter id.
    # (No mkdir here: persist_rendered owns file writes and degrades gracefully
    # on read-only filesystems.)
    row = session.query(NewsletterRow).filter_by(date=date_str, niche_id=niche_id).one_or_none()
    if row is None:
        row = NewsletterRow(date=date_str, niche_id=niche_id, subject="", status="built")
        session.add(row)
        session.flush()
    content = compose_content(
        niche, date_str, analysis, diagnostics, key_to_db_id, row.id, newsletter_cfg
    )
    result = persist_rendered(
        session,
        settings,
        niche_id,
        date_str,
        content.subject,
        content,
        {"analysis": analysis.model_dump(), "diagnostics": diagnostics or {}},
    )
    return result
