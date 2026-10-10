"""Phase 5: composer + templates + file output (stub analysis, tmp dirs)."""

from __future__ import annotations

from pathlib import Path

from newsletter_machine.config import NewsletterConfig, NicheConfig
from newsletter_machine.llm.local_stub import StubLLMClient
from newsletter_machine.llm.schemas import AnalysisResult
from newsletter_machine.pipeline.analyze import ground_analysis
from newsletter_machine.pipeline.compose import (
    build_newsletter,
    compose_content,
    compose_digest,
    render_html,
    render_markdown,
    render_text,
)


def _niche() -> NicheConfig:
    return NicheConfig(id="ai", name="AI tools")


def _cfg(**overrides) -> NewsletterConfig:
    base = {
        "name": "Daily Signal",
        "tagline": "tag",
        "sections_order": [
            "tldr",
            "top_stories",
            "trend_radar",
            "platform_highlights",
            "voices",
            "questions",
            "opportunities",
            "action",
            "coverage",
        ],
        "sections": {
            s: {"enabled": True, "max_items": 5}
            for s in [
                "tldr",
                "top_stories",
                "trend_radar",
                "platform_highlights",
                "voices",
                "questions",
                "opportunities",
                "action",
                "coverage",
            ]
        },
        "subject_style": "{date} — {niche}: top stories",
    }
    base.update(overrides)
    return NewsletterConfig.model_validate(base)


async def _analysis() -> AnalysisResult:
    payload = {
        "niche": {"id": "ai", "name": "AI tools"},
        "date": "2026-10-10",
        "items": [
            {
                "key": "blogs:a",
                "platform": "blogs",
                "url": "https://example.com/a",
                "title": "Story A",
                "text": "Body A here today.",
                "author": "Ann",
                "score": 0.9,
                "cluster": "ai",
            },
            {
                "key": "blogs:b",
                "platform": "blogs",
                "url": "https://example.com/b",
                "title": "Story B",
                "text": "Body B here today.",
                "author": "Bob",
                "score": 0.5,
                "cluster": "ai",
            },
        ],
        "clusters": [{"label": "ai", "momentum": "rising", "keys": ["blogs:a", "blogs:b"]}],
        "coverage": {"blogs": 2},
        "total_items": 2,
    }
    raw = await StubLLMClient().analyze(payload)
    result, _ = ground_analysis(raw, payload)
    return result


async def test_compose_subject_sections_and_feedback_links() -> None:
    analysis = await _analysis()
    content = compose_content(
        _niche(), "2026-10-10", analysis, {"stats": {}}, {"blogs:a": 11}, 7, _cfg()
    )
    assert content.subject == "2026-10-10 — AI tools: top stories"
    assert content.preheader
    assert content.top_stories[0].feedback_up == "/feedback?newsletter_id=7&item_id=11&signal=up"
    assert content.top_stories[0].feedback_down.endswith("signal=down")
    assert "top_stories" in content.enabled_sections


async def test_disabled_section_and_caps() -> None:
    analysis = await _analysis()
    cfg = _cfg()
    cfg.sections["voices"].enabled = False
    cfg.sections["top_stories"].max_items = 1
    content = compose_content(_niche(), "2026-10-10", analysis, {}, {}, None, cfg)
    assert "voices" not in content.enabled_sections
    assert len(content.top_stories) == 1
    html = render_html(content)
    assert "Voices" not in html
    assert "Story A" in html


async def test_all_formats_render() -> None:
    analysis = await _analysis()
    content = compose_content(_niche(), "2026-10-10", analysis, {}, {}, None, _cfg())
    html, markdown, text = render_html(content), render_markdown(content), render_text(content)
    assert "<html" in html and "Story A" in html
    assert 'style="' in html  # premailer inlined the CSS
    assert "@media" in html  # ...but kept the dark-mode query
    assert "## TL;DR" in markdown and "Story A" in markdown
    assert "TOP STORIES" in text and "Story A" in text
    assert "https://example.com/a" in html and "https://example.com/a" in text


async def test_build_newsletter_writes_files_and_upserts(tmp_path: Path) -> None:
    from newsletter_machine.config import Settings
    from newsletter_machine.db.models import Base, Newsletter
    from newsletter_machine.db.session import get_engine, make_session_factory

    settings = Settings(
        _env_file=None,
        database_url="sqlite:///:memory:",  # type: ignore[call-arg]
        output_dir=str(tmp_path / "out"),
    )
    engine = get_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session = make_session_factory(engine)()
    try:
        analysis = await _analysis()
        first = build_newsletter(
            session, settings, _niche(), "2026-10-10", analysis, {}, {}, _cfg()
        )
        second = build_newsletter(
            session, settings, _niche(), "2026-10-10", analysis, {}, {}, _cfg()
        )
        assert first["id"] == second["id"]  # idempotent upsert
        assert session.query(Newsletter).count() == 1
        for key in ("html_path", "md_path", "txt_path"):
            assert Path(first[key]).exists()
        assert "AI tools" in Path(first["html_path"]).read_text(encoding="utf-8")
    finally:
        session.close()


async def test_build_newsletter_survives_readonly_fs(tmp_path: Path) -> None:
    from newsletter_machine.config import Settings
    from newsletter_machine.db.models import Base, Newsletter
    from newsletter_machine.db.session import get_engine, make_session_factory

    blocker = tmp_path / "blocker"
    blocker.write_text("not a dir", encoding="utf-8")
    settings = Settings(
        _env_file=None,
        database_url="sqlite:///:memory:",  # type: ignore[call-arg]
        output_dir=str(blocker / "out"),
    )
    engine = get_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session = make_session_factory(engine)()
    try:
        analysis = await _analysis()
        result = build_newsletter(
            session, settings, _niche(), "2026-10-10", analysis, {}, {}, _cfg()
        )
        assert result["html_path"] == ""
        assert session.query(Newsletter).count() == 1
    finally:
        session.close()


async def test_digest_merges_niches() -> None:
    analysis = await _analysis()
    first = compose_content(_niche(), "2026-10-10", analysis, {}, {}, 1, _cfg())
    other_niche = NicheConfig(id="travel", name="Travel")
    second = compose_content(other_niche, "2026-10-10", analysis, {}, {}, 2, _cfg())
    digest = compose_digest([first, second], "2026-10-10", _cfg())
    assert digest.niche_id == "digest"
    assert "All niches" in digest.subject
    assert any("[Travel]" in bullet for bullet in digest.tldr)
    assert len(digest.top_stories) == 4
    assert digest.coverage == {"AI tools": 2, "Travel": 2}
