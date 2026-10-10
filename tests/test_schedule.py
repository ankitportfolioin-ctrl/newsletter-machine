"""Phase 6: scheduler registration + per-niche fault isolation (no waiting)."""

import pytest

from newsletter_machine.config import NewsletterConfig
from newsletter_machine.scheduler import build_scheduler, run_daily


def _cfg(**overrides) -> NewsletterConfig:
    base: dict = {"name": "T", "send_time": "07:00", "timezone": "UTC"}
    base.update(overrides)
    return NewsletterConfig.model_validate(base)


def test_scheduler_registers_daily_cron() -> None:
    scheduler = build_scheduler(None, _cfg())
    jobs = scheduler.get_jobs()
    assert len(jobs) == 1 and jobs[0].id == "daily-newsletter"
    trigger = jobs[0].trigger
    fields = {f.name: str(f) for f in trigger.fields}
    assert fields["hour"] == "7" and fields["minute"] == "0"


def test_bad_send_time_falls_back() -> None:
    scheduler = build_scheduler(None, _cfg(send_time="nonsense"))
    fields = {f.name: str(f) for f in scheduler.get_jobs()[0].trigger.fields}
    assert fields["hour"] == "7"


def test_run_daily_isolates_niche_failures(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    import yaml

    from newsletter_machine.config import clear_config_cache

    (tmp_path / "niches.yaml").write_text(
        yaml.safe_dump({"niches": [{"id": "good", "name": "Good"}, {"id": "bad", "name": "Bad"}]}),
        encoding="utf-8",
    )
    (tmp_path / "sources.yaml").write_text(yaml.safe_dump({"collectors": {}}), encoding="utf-8")
    (tmp_path / "newsletter.yaml").write_text(
        yaml.safe_dump({"newsletter": {"name": "T", "delivery_method": "none"}}), encoding="utf-8"
    )
    monkeypatch.setenv("NICHES_YAML", str(tmp_path / "niches.yaml"))
    monkeypatch.setenv("SOURCES_YAML", str(tmp_path / "sources.yaml"))
    monkeypatch.setenv("NEWSLETTER_YAML", str(tmp_path / "newsletter.yaml"))
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path}/t.db")
    monkeypatch.setenv("LLM_PROVIDER", "stub")
    clear_config_cache()
    try:
        import newsletter_machine.collectors.runner as runner_mod
        import newsletter_machine.pipeline.build_flow as flow_mod
        import newsletter_machine.pipeline.deliver as deliver_mod

        async def fake_collect(settings, since, niche_id=None, **kwargs):
            if niche_id == "bad":
                raise RuntimeError("collector boom")
            return {"runs": [], "inserted": 0, "skipped": 0}

        async def fake_build(
            session, settings, niche_cfg, newsletter_cfg, date_str, client, **kwargs
        ):
            return {"id": 99, "subject": "stubbed", "niche_id": niche_cfg.id}

        async def fake_deliver(session, settings, newsletter_cfg, newsletter_id, **kwargs):
            return {"method": "none", "skipped": True}

        monkeypatch.setattr(runner_mod, "collect_and_store", fake_collect)
        monkeypatch.setattr(flow_mod, "build_niche_newsletter", fake_build)
        monkeypatch.setattr(deliver_mod, "deliver_newsletter", fake_deliver)
        outcomes = run_daily(since_hours=1)
        assert outcomes["niches"]["bad"]["collect_error"] == "RuntimeError: collector boom"
        assert outcomes["niches"]["good"]["newsletter_id"] == 99
        assert outcomes["niches"]["good"]["delivery"] == {"method": "none", "skipped": True}
    finally:
        clear_config_cache()
