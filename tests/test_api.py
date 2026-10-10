"""Phase 6: JSON API + dashboard tests (temp DB, token auth, respx feeds)."""

from __future__ import annotations

from pathlib import Path

import pytest
import respx
from fastapi.testclient import TestClient
from httpx import Response

from newsletter_machine.api.main import create_app
from newsletter_machine.config import clear_config_cache

TOKEN = "test-token-123"
HEADERS = {"X-API-Token": TOKEN}
FIX = Path(__file__).parent / "fixtures"


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    import yaml

    (tmp_path / "niches.yaml").write_text(
        yaml.safe_dump(
            {
                "niches": [
                    {
                        "id": "n1",
                        "name": "Niche One",
                        "targets": {"blog_feeds": ["https://feed.example.com/rss.xml"]},
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "sources.yaml").write_text(
        yaml.safe_dump({"collectors": {"blogs": {"enabled": True, "tier": "rss"}}}),
        encoding="utf-8",
    )
    (tmp_path / "newsletter.yaml").write_text(
        yaml.safe_dump({"newsletter": {"name": "Test Signal"}}), encoding="utf-8"
    )
    monkeypatch.setenv("NICHES_YAML", str(tmp_path / "niches.yaml"))
    monkeypatch.setenv("SOURCES_YAML", str(tmp_path / "sources.yaml"))
    monkeypatch.setenv("NEWSLETTER_YAML", str(tmp_path / "newsletter.yaml"))
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 't.db'}")
    monkeypatch.setenv("API_TOKEN", TOKEN)
    clear_config_cache()
    test_client = TestClient(create_app())
    # Seed one niche row for CRUD tests that need existing data.
    test_client.post("/niches", json={"id": "seed", "name": "Seed"}, headers=HEADERS)
    yield test_client
    clear_config_cache()


def test_health_open_and_auth_required(client: TestClient) -> None:
    assert client.get("/health").status_code == 200
    assert client.get("/health").json()["status"] == "ok"
    assert client.get("/niches").status_code == 401
    assert client.get("/niches?token=wrong").status_code == 401
    assert client.get("/niches", headers=HEADERS).status_code == 200
    assert client.get("/niches?token=" + TOKEN).status_code == 200


def test_niches_crud_and_delete_guard(client: TestClient) -> None:
    created = client.post("/niches", json={"id": "n1", "name": "Niche One"}, headers=HEADERS)
    assert created.status_code == 201
    assert created.json()["created"] is True
    again = client.post("/niches", json={"id": "n1", "name": "Renamed"}, headers=HEADERS)
    assert again.json()["created"] is False
    patched = client.patch("/niches/n1", json={"description": "d"}, headers=HEADERS)
    assert patched.json()["niche"]["name"] == "Renamed"
    assert client.get("/niches/ ghost".replace(" ", ""), headers=HEADERS).status_code == 404
    assert client.get("/niches/n1", headers=HEADERS).json()["item_count"] == 0
    assert client.delete("/niches/n1", headers=HEADERS).json() == {"deleted": "n1"}

    # Niche with items cannot be deleted (409).
    from newsletter_machine.api.deps import session_factory_for
    from newsletter_machine.config import get_settings
    from newsletter_machine.db.models import Item

    factory = session_factory_for(get_settings().database_url)
    with factory() as session:
        session.add(
            Item(platform="blogs", external_id="e", url="https://example.com/e", niche_id="seed")
        )
        session.commit()
    assert client.delete("/niches/seed", headers=HEADERS).status_code == 409


def test_sources_status_lists_collectors(client: TestClient) -> None:
    body = client.get("/sources", headers=HEADERS).json()["sources"]
    names = {s["platform"] for s in body}
    assert {"blogs", "youtube", "reddit", "x", "linkedin", "instagram", "quora"} <= names
    quora = next(s for s in body if s["platform"] == "quora")
    assert quora["live_tier"] == "manual"
    assert "official API" in quora["note"]


@respx.mock
def test_trigger_run_collects_and_lists(client: TestClient) -> None:
    feed_xml = (FIX / "sample_feed.xml").read_bytes()
    article_html = (FIX / "sample_article.html").read_text(encoding="utf-8")
    respx.get("https://feed.example.com/rss.xml").mock(
        return_value=Response(
            200, content=feed_xml, headers={"content-type": "application/rss+xml"}
        )
    )
    respx.get("https://example.com/blog/post-1").mock(
        return_value=Response(200, text=article_html, headers={"content-type": "text/html"})
    )
    respx.get("https://example.com/blog/post-2").mock(return_value=Response(404, text="nope"))
    resp = client.post(
        "/runs",
        json={"niche": "n1", "platforms": ["blogs"], "since_hours": 8760, "limit": 5},
        headers=HEADERS,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["inserted"] >= 1
    runs = client.get("/runs?niche_id=n1", headers=HEADERS).json()["runs"]
    assert len(runs) >= 1
    assert runs[0]["stats"]["blogs"]["tier_used"] == "rss"
    assert client.get("/runs/999999", headers=HEADERS).status_code == 404
    bad = client.post("/runs", json={"niche": "ghost"}, headers=HEADERS)
    assert bad.status_code == 404


def _seed_newsletter(client: TestClient) -> int:
    from newsletter_machine.api.deps import session_factory_for
    from newsletter_machine.config import get_settings
    from newsletter_machine.db.models import Newsletter

    factory = session_factory_for(get_settings().database_url)
    with factory() as session:
        row = Newsletter(
            date="2026-10-10",
            niche_id="n1",
            subject="Seeded",
            html_path="",
            md_path="",
            txt_path="",
            content_json={},
            status="built",
        )
        session.add(row)
        session.commit()
        return row.id


def test_newsletters_list_and_preview(client: TestClient, tmp_path: Path) -> None:
    newsletter_id = _seed_newsletter(client)
    from newsletter_machine.api.deps import session_factory_for
    from newsletter_machine.config import get_settings

    html_file = tmp_path / "preview.html"
    html_file.write_text("<html><body><h1>Seeded</h1></body></html>", encoding="utf-8")
    factory = session_factory_for(get_settings().database_url)
    with factory() as session:
        from newsletter_machine.db.models import Newsletter

        row = session.get(Newsletter, newsletter_id)
        assert row is not None
        row.html_path = str(html_file)
        session.commit()
    listing = client.get("/newsletters", headers=HEADERS).json()["newsletters"]
    assert any(n["id"] == newsletter_id for n in listing)
    preview = client.get(f"/newsletters/{newsletter_id}/preview", headers=HEADERS)
    assert preview.status_code == 200
    assert "Seeded" in preview.text
    assert client.get("/newsletters/999999/preview", headers=HEADERS).status_code == 404


def test_feedback_post_get_stats(client: TestClient) -> None:
    newsletter_id = _seed_newsletter(client)
    created = client.post(
        "/feedback", json={"newsletter_id": newsletter_id, "signal": "up"}, headers=HEADERS
    )
    assert created.status_code == 201
    bad_signal = client.post("/feedback", json={"signal": "meh"}, headers=HEADERS)
    assert bad_signal.status_code == 422
    bad_ref = client.post(
        "/feedback", json={"newsletter_id": 999999, "signal": "up"}, headers=HEADERS
    )
    assert bad_ref.status_code == 404
    stats = client.get("/feedback/stats", headers=HEADERS).json()
    assert stats["total"] == 1 and stats["by_signal"] == {"up": 1}
    # Email-link friendly GET intake.
    thanks = client.get(f"/feedback?newsletter_id={newsletter_id}&signal=down&token={TOKEN}")
    assert thanks.status_code == 200 and "not useful" in thanks.text
    stats2 = client.get("/feedback/stats", headers=HEADERS).json()
    assert stats2["total"] == 2


def test_dashboard_pages(client: TestClient) -> None:
    for path in (
        "/dashboard",
        "/dashboard/niches",
        "/dashboard/sources",
        "/dashboard/runs",
        "/dashboard/newsletters",
        "/dashboard/feedback",
        "/dashboard/feedback/partial",
    ):
        resp = client.get(path, headers=HEADERS)
        assert resp.status_code == 200, path
        assert "Newsletter Machine" in resp.text or "Feedback" in resp.text or "<table" in resp.text
    assert (
        'hx-get="/dashboard/feedback/partial'
        in client.get("/dashboard/feedback", headers=HEADERS).text
    )
    assert client.get("/dashboard").status_code == 401  # auth enforced on HTML too


def test_dashboard_niche_form_and_trigger(client: TestClient) -> None:
    created = client.post(
        "/dashboard/niches?token=" + TOKEN,
        data={"id": "web", "name": "Web Niche", "description": ""},
    )
    assert created.status_code in (200, 303)  # TestClient follows the 303 redirect
    assert "Web Niche" in created.text
    assert client.get("/niches/web", headers=HEADERS).status_code == 200
    deleted = client.post("/dashboard/niches/web/delete?token=" + TOKEN)
    assert deleted.status_code in (200, 303)
    assert client.get("/niches/web", headers=HEADERS).status_code == 404


def test_trigger_build_renders_newsletter(client: TestClient) -> None:
    from datetime import UTC, datetime

    from newsletter_machine.api.deps import session_factory_for
    from newsletter_machine.config import get_settings
    from newsletter_machine.db.models import Item, Newsletter

    factory = session_factory_for(get_settings().database_url)
    with factory() as session:
        session.add(
            Item(
                platform="blogs",
                external_id="b1",
                url="https://example.com/b1",
                canonical_url="https://example.com/b1",
                title="Build trigger story",
                text="Enough body words here to analyze properly in this test run.",
                published_at=datetime.now(UTC),
                niche_id="n1",
            )
        )
        session.commit()
    resp = client.post(
        "/newsletters/build",
        json={"niche": "n1", "date": "2026-10-10", "since_hours": 8760},
        headers=HEADERS,
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["date"] == "2026-10-10"
    assert body["built"][0]["niche_id"] == "n1"
    assert body["built"][0]["html_path"].endswith("newsletter.html")
    with factory() as session:
        assert session.query(Newsletter).filter_by(niche_id="n1").count() == 1
    assert (
        client.post("/newsletters/build", json={"niche": "ghost"}, headers=HEADERS).status_code
        == 404
    )
    bad_date = client.post("/newsletters/build", json={"date": "yesterday"}, headers=HEADERS)
    assert bad_date.status_code == 400
