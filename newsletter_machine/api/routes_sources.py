"""Source status (read-only): configured tiers + live credential availability.

Sources are config-file managed (config/sources.yaml); this endpoint reports
effective status for the dashboard and `doctor`. Toggling belongs in the YAML.
"""

from __future__ import annotations

import os

from fastapi import APIRouter, Depends

from newsletter_machine.api.deps import current_settings, require_token
from newsletter_machine.collectors.registry import available_collectors
from newsletter_machine.config import Settings, load_sources

router = APIRouter(dependencies=[Depends(require_token)])


@router.get("/sources")
def list_sources(settings: Settings = Depends(current_settings)) -> dict:
    sources = load_sources(settings)
    collectors = available_collectors()
    out = []
    for name in sorted(collectors):
        cfg = sources.collectors.get(name)
        try:
            live_tier, note = collectors[name]().tier_status()
        except Exception as e:  # noqa: BLE001 - status must never 500
            live_tier, note = "disabled", f"status check failed: {e}"
        out.append(
            {
                "platform": name,
                "enabled": bool(cfg.enabled) if cfg else True,
                "configured_tier": cfg.tier if cfg else None,
                "live_tier": live_tier,
                "note": note,
                "credential_env_vars": list(cfg.credential_env_vars) if cfg else [],
                "credentials_present": {
                    var: bool(os.getenv(var)) for var in (cfg.credential_env_vars if cfg else [])
                },
                "rate_limit_per_min": cfg.rate_limit_per_min if cfg else None,
                "item_cap_per_run": cfg.item_cap_per_run if cfg else None,
            }
        )
    return {"sources": out}
