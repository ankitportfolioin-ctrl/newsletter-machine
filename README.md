# Newsletter Machine

Daily multi-platform newsletter generator: collect from Instagram, YouTube, LinkedIn,
X, Reddit, Quora and blogs for user-defined niches, then rank, cluster, analyze and
deliver a newsletter (HTML + Markdown + plain text).

> **Status: all 8 phases complete.** `run --demo` works with zero keys and zero
> network; live collection works keyless for RSS; key-gated paths degrade
> gracefully with honest diagnostics. See `PROGRESS.md` for the verified /
> fixture-tested / needs-credentials breakdown.

## Architecture

```
config/niches.yaml ─┐
config/sources.yaml ─┼─▶ collect (7 tiered collectors, polite HTTP)
.env (secrets) ──────┘         │  official API → RSS → provider → manual
                               ▼
                     normalize → dedupe (canonical + SimHash) → score (6 factors)
                               ▼
                     cluster (TF-IDF topics) → LLM analysis (validated, grounded)
                               ▼
                     compose (HTML/MD/TXT) → deliver (file/smtp/resend/webhook)
                               ▼
                     SQLite (items, scores, clusters, runs, newsletters, feedback)
                               ▲
               FastAPI + dashboard (niches, sources, runs, preview, feedback)
```

See `Architecture.md` for the original pipeline sketch. Data flow per niche per
day: `collect` stores items idempotently → `build` scores/clusters/analyzes/
renders → `send` delivers → `schedule`/`run` automate the whole day.

## Quickstart (Phase 5)

```powershell
# 0. Zero-key demo (no network, no credentials): seeds fixtures, builds a sample
uv run newsletter-machine run --demo
# or: make demo

# 1. Install (uv preferred, venv+pip fallback)
uv sync --group dev
# fallback: python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -e "."
# or: make install

# 2. Initialize
uv run newsletter-machine init
uv run newsletter-machine doctor

# 3. Collect (blogs/RSS needs no keys; YouTube/Reddit degrade gracefully)
uv run newsletter-machine collect --platforms blogs --limit 5 --since-hours 168

# 4. Manual import for anything without a feed/API
uv run newsletter-machine collect --niche ai-tools-marketers --platforms manual --manual-file my-links.csv

# 5. Build newsletters (stub analysis by default; --llm anthropic/openai with keys)
uv run newsletter-machine build --since-hours 168
uv run newsletter-machine build --niche ai-tools-marketers --date 2026-10-10 --digest

# 6. Tests + lint
uv run pytest -q
uv run ruff check .
```

## Configuration

- Secrets: `.env` (copy from `.env.example`). Never commit `.env`.
- Niches: `config/niches.yaml` (2 examples: `ai-tools-marketers`, `sustainable-travel`).
- Sources/tiers: `config/sources.yaml`.
- Newsletter shape: `config/newsletter.yaml`.
- Env overrides: `NICHES_YAML`, `SOURCES_YAML`, `NEWSLETTER_YAML`, `DATABASE_URL`.

## Credential guide

| Platform | Tier now | How to get it / cost / limits |
|---|---|---|
| Blogs/RSS | `rss` (no key) | Put feed URLs in `niches.yaml` (`targets.blog_feeds`). If a feed 404s, the collector tries `<domain>/sitemap.xml` and keeps article-like URLs only (assets filtered). Sites with no feed: use manual import. |
| YouTube | `official_api`, `rss` fallback | Key: Google Cloud Console → enable **YouTube Data API v3** → API key → `YOUTUBE_API_KEY`. Free quota 10,000 units/day (≈100 search calls; `search.list` costs 100, `videos.list` ~1 — we report estimates). No key? List channel IDs (`UC…`) in `youtube_channels` for the public channel-RSS fallback (no view counts). No transcripts are fetched (Data API has none; we store descriptions). |
| Reddit | `official_api`, `public_json` fallback | OAuth: reddit.com/prefs/apps → **script** app → `REDDIT_CLIENT_ID` + `REDDIT_CLIENT_SECRET` (free, 60 req/min OAuth). No creds? Public `hot.json` fallback at polite rates (no keyword search; 429s recorded, never crash). |
| X | `official_api` → `provider` → `manual` | Bearer token: X Developer Portal → project + app → `X_BEARER_TOKEN`. **Search needs a paid tier (Basic $100/mo+): free tokens get HTTP 402/403**, which we record and fall through — never crash. Without a token: provider or `--manual-file … --manual-platform x`. No scraping, ever. |
| LinkedIn | `official_api` (verify-only) → `provider` → `manual` | Token: LinkedIn Developer → app with `openid profile` scope → `LINKEDIN_ACCESS_TOKEN`. **The official API has no public/keyword post search** — we verify the token via OpenID `/v2/userinfo` (proves it works) and say so in the errors. Content comes from a provider or `--manual-file … --manual-platform linkedin`. |
| Instagram | `official_api` (own account) → `provider` → `manual` | Graph API: Meta app + Facebook-login business/creator account → `INSTAGRAM_ACCESS_TOKEN` + `INSTAGRAM_BUSINESS_ID`. Fetches **your own account's** recent media, filtered by niche hashtags/keywords. Hashtag search needs an approved app (not attempted). Without creds: provider or `--manual-file … --manual-platform instagram`. |
| Quora | `provider` → `manual` (no official API) | **Verified 2026-10-10: Quora has no API and no public topic RSS** (topic pages return HTTP 403 to bots). Use a provider or `--manual-file … --manual-platform quora`. Setting `tier: rss` attempts `{topic}/rss` once per topic and records the (expected) failure. |
| Manual | `manual` | Any platform: `collect --manual-file links.csv --manual-platform quora`. CSV needs a `url` header column; JSON accepts a list or `{"items": [...]}`; `.txt` is one URL per line. |

ToS notes: official APIs + public RSS only; per-collector rate limits
(`sources.yaml: rate_limit_per_min`), 3-attempt exponential backoff on
429/5xx, honest `User-Agent`. Nothing bypasses logins, CAPTCHAs or paywalls.
Respect `robots.txt` intent: the sitemap fallback only reads published
sitemaps; full-text extraction fetches pages a normal reader could open.

## Provider fallback (one interface for all restricted platforms)

Set `PROVIDER_BASE_URL` (+ optional `PROVIDER_API_KEY`) to point every
Phase-3 collector at a single third-party JSON API (e.g. an Apify actor you
run, Bright Data, or an in-house endpoint). The collector POSTs
`{"platform", "queries", "since", "limit"}` and maps `{"items": [{url*,
title, text, author, published_at, metrics, …}]}` — `url` is the only required
field. Any extra keys are ignored; rows without `url` are skipped, not fatal.
See `newsletter_machine/collectors/providers/generic.py` for the exact schema.
Providers must source data lawfully — this code only maps their JSON, and the
newsletter footer always reports `tier_used: provider` so readers know where
items came from.

## CLI (Phase 6)

- `newsletter-machine init [--force]` — create `.env` + DB + sync niches.
- `newsletter-machine doctor` — honest env/DB/config/collector table.
- `newsletter-machine collect [...]` — run collectors, idempotent upsert, Run rows.
- `newsletter-machine build [...] [--digest]` — pipeline + analysis + render to `output/newsletters/`.
- `newsletter-machine send --newsletter ID [--method file|smtp|resend|webhook|none] [--to a@x,b@y]` — deliver a built newsletter (default method from `newsletter.yaml`).
- `newsletter-machine serve [--host 127.0.0.1 --port 8000]` — API + dashboard.
- `newsletter-machine schedule` — daily collect→build→deliver cron (blocking).
- `run` — full-pipeline demo mode lands in Phase 7.

## API + dashboard (Phase 6)

```powershell
uv run newsletter-machine serve --port 8000
# JSON API:  /health (open) + everything else needs the token:
#   X-API-Token: <API_TOKEN>  (or Authorization: Bearer, or ?token=)
#   GET/POST/PATCH/DELETE /niches · GET /sources · GET/POST /runs
#   GET /newsletters · GET /newsletters/{id}/preview
#   POST /feedback (JSON) · GET /feedback?...&signal=up (email links) · GET /feedback/stats
# Dashboard: /dashboard (same token, ?token= works for browsers)
```

Auth is a single shared secret (`API_TOKEN` in `.env`) — fine for localhost
and small teams behind TLS, not for hostile exposure. Sources are read-only
in the API (tiers live in `config/sources.yaml`); niches are DB CRUD (YAML
`init`/`collect` sync overwrites name/description — documented precedence).
`POST /runs` executes collection inline and returns the summary (slow on
first contact with rate limits — dashboard trigger included). Newsletter
feedback links point at `GET /feedback`, which records the vote and returns a
thanks page.

## Delivery + scheduler (Phase 6)

- `delivery_method` in `newsletter.yaml`: `file` (default, always works),
  `smtp` (STARTTLS via `SMTP_*`), `resend` (`RESEND_API_KEY`), `webhook`
  (`DELIVERY_WEBHOOK_URL` posts subject+HTML+text), `none`. Recipients from
  `recipients` or `--to`. Every send stamps a receipt into the newsletter's
  `content_json.delivery` and marks it `delivered`.
- `schedule` runs one cron job at `send_time`/`timezone` from
  `newsletter.yaml`: collect (24h window) → build → deliver per niche, one
  niche's failure never stops the others. Same entry point works under
  cron/systemd — see `scheduler.run_daily()`.

## LLM analysis (Phase 5)

`LLM_PROVIDER=stub` (default, deterministic, extractive — safe for tests and
demos) or `anthropic` / `openai` with keys (`ANTHROPIC_API_KEY` /
`OPENAI_API_KEY`; models via `ANTHROPIC_MODEL`/`OPENAI_MODEL`, defaults
`claude-3-5-haiku-20241022` / `gpt-4o-mini`). Real clients use plain httpx
(no SDK deps), 3-attempt backoff, and up to 3 validation retries on bad JSON.
Whatever the provider, output must validate against `llm/schemas.py`, and the
grounding step drops any claim pointing at unknown items — fabricated quotes
(text not found verbatim in the cited item) are dropped too, with counts in
the diagnostics footer. Momentum labels (rising/steady/fading) are computed
from cluster member ages, never hallucinated.

## Adding a niche / collector (Phase 2)

- New niche: append to `config/niches.yaml` (id, name, keywords, `targets.*`), run `init` (syncs DB) then `collect --niche <id> --platforms blogs`.
- New collector: subclass `BaseCollector` in `newsletter_machine/collectors/`, register the `(module, Class)` path in `registry._COLLECTOR_PATHS`, add a `sources.yaml` entry, use `collectors/http.py` (`create_client`, `get_limiter`, `polite_get`) so limits/retries come free, and add a fixture-based test. The runner catches everything, but `collect` itself must also catch per-feed/per-call errors into `errors`.

## Pipeline: scoring, dedupe, clustering (Phase 4)

`run_pipeline(niche, docs, session)` in `newsletter_machine/pipeline/run.py`
(normalize → dedupe → score → cluster; scores/clusters persisted, full ranked
list returned for audit).

- **Dedupe:** exact canonical-URL match, then SimHash (vendored, 64-bit,
  title triple-weighted) with Hamming ≤ 8 — calibrated on
  `tests/fixtures/pipeline_items.json` (true repost = 6, closest non-dupe =
  21). First occurrence wins; removals reported with reasons.
- **Score:** `w1·recency (48h half-life) + w2·engagement velocity, min-max
  normalized per platform + w3·source authority + w4·keyword relevance
  (title×2, exclude-hit→0) + w5·novelty (unseen canonical in 7d) +
  w6·feedback prior`. Defaults 0.25/0.25/0.15/0.25/0.05/0.05; override per
  niche via `weight_overrides` in `niches.yaml`. Every component is stored in
  `item_scores` — no black box.
- **Threshold:** `above_threshold` = total ≥ `min_score` AND relevance > 0, so
  excluded/off-topic heat never passes on virality alone.
- **Clusters:** pure-Python TF-IDF + single-link agglomeration (cosine ≥
  0.22), labels = top-3 terms. Summaries and momentum notes come from the
  Phase 5 LLM layer.

## Troubleshooting

- `Config file not found`: check `NICHES_YAML`/`SOURCES_YAML`/`NEWSLETTER_YAML` or run from repo root.
- `database ERROR` in doctor: check `DATABASE_URL`; default SQLite file is created by `init`.
- Collector shows "missing KEY": set it in `.env` (Phase 2+ will use it).
- `build` finds no items: run `collect` first (or widen `--since-hours`); items need `published_at` inside the window (undated items are always included).
- `send` fails on SMTP: verify `SMTP_HOST/PORT/USER/PASSWORD/FROM` and recipients (`newsletter.recipients` or `--to`); start with `--method file`.
- API 401s: set `API_TOKEN` in `.env` and pass it as `X-API-Token` (dashboard: `?token=`).
- Scheduler timezone errors: install `tzdata` (Docker image includes it) or use `timezone: UTC`.
- Docker daemon not running: `docker build`/`up` need Docker Desktop/Engine; everything else runs natively via `uv`.

## Environment reference (`.env`, see `.env.example`)

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./newsletter_machine.db` | SQLite file or Postgres URL (same code path) |
| `API_TOKEN` | `change-me-dev-token` | Shared secret for API + dashboard (change it) |
| `LLM_PROVIDER` | `stub` | `stub` (deterministic) \| `anthropic` \| `openai` |
| `LOG_LEVEL` / `LOG_FORMAT` | `INFO` / `text` | `json` lines for Docker/scheduler ingestion |
| `OUTPUT_DIR` | `output/newsletters` | Rendered newsletter files |
| `NICHES_YAML` / `SOURCES_YAML` / `NEWSLETTER_YAML` | `config/*.yaml` | Config overrides (tests use these) |
| Platform keys | empty | `YOUTUBE_API_KEY`, `REDDIT_*`, `X_BEARER_TOKEN`, `LINKEDIN_*`, `INSTAGRAM_*`, `PROVIDER_*`, `ANTHROPIC_/OPENAI_API_KEY`, `SMTP_*`, `RESEND_API_KEY` |
