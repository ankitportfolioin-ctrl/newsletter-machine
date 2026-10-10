# PROGRESS.md — Newsletter Machine

## Deploy migration: Supabase + GitHub + Vercel (IN PROGRESS, code done 2026-10-10)

### Code changes (done, verified locally)
- `psycopg[binary]` dependency (engine creation against a postgres URL proven
  offline); `.env.example` documents pooler (`:6543`) vs direct (`:5432`) URLs
  with the required `postgresql+psycopg://` prefix; SQLite default untouched.
- Vercel: root `api/index.py` re-export (verified identical object),
  minimal `vercel.json`, generated `requirements.txt` (193 lines, psycopg
  included), `.python-version` 3.12, `[tool.vercel] entrypoint` backup.
- Serverless hardening: file writes degrade to DB-only with warning (tested);
  preview re-renders from stored analysis when files are absent (tested).
- Tests: `test_deploy.py` (entrypoint identity, read-only-FS persist,
  DB-backed preview, Postgres roundtrip gated on `TEST_DATABASE_URL`).
- Local git: `init` + 2 commits, secrets excluded (`.env`/`*.db`/venv absent
  from the tree — verified before each commit).

### Done in this session
- `uv run pytest -q` → **126 passed, 4 skipped** (3 key-gated + Postgres).
- `uv run ruff check .` → clean.

### WAITING ON HUMAN (manual steps, in order)
1. **Supabase**: create project as `ankit.portfolio.in@gmail.com`, copy the
   session-pooler URL → run `TEST_DATABASE_URL=<url> pytest tests/test_deploy.py`
   (or hand me the URL and I'll run it — prefer pooler URL; don't commit it).
2. **GitHub**: `gh auth login` (browser, same account) → I push (repo
   `newsletter-machine`, public, already committed locally). Alternative: paste
   a fine-grained PAT and I'll push via git immediately.
3. **Vercel**: import the repo, set `DATABASE_URL` (pooler) + `API_TOKEN` (+
   optional LLM keys), deploy, open `/health` and `/dashboard?token=...`.
   Full step-by-step now lives in README "Deploy: Supabase + GitHub + Vercel".

## Phase 8 — Final audit (COMPLETE, verified 2026-10-10)

### Audit runs (real output summary)
- `uv run ruff check .` → **All checks passed!**
- `uv run pytest -q` → **123 passed, 3 skipped** (skips: live YouTube, live
  Reddit, live LLM — all key-gated, all print their skip reason).
- Fixture E2E determinism: `run --demo --date 2026-10-10` twice on scratch →
  identical SHA256 for HTML/MD/TXT across rebuilds; 0 dupes on reseed.
- Structure audit: every file from the spec's PROJECT STRUCTURE exists
  (collectors ×7 + providers + manual_import, pipeline ×7, llm ×4, api ×6,
  templates ×3 + dashboard ×8, config ×3, tests, Makefile, Dockerfile,
  compose, pyproject, .env.example); extras are additive (deps, build_flow,
  run, demo, logging, factory, prompts, generic provider, http, runner).
- Secret audit (regex sweep for keys/tokens/passwords): only `fixture-key`,
  `test-token-*` and the documented `change-me-dev-token` placeholder; `.env`
  holds defaults only; `.env` + `*.db` gitignored. No real credentials anywhere.
- Outbound-HTTP audit: all 6 raw `client.get/post` sites are inside retry
  wrappers or behind `limiter.acquire()` — every collector/provider/LLM/
  delivery call is rate-limited + backed off. No scraping, no login/CAPTCHA
  bypass, no Playwright (intentionally absent — never needed).
- Workspace hygiene: found and killed leftover Phase 6 uvicorn processes +
  deleted their temp files; root now holds only deliverables + gitignored
  runtime artifacts.

### VERIFIED (ran live on this machine, real output seen)
- Scaffold/config/DB/CLI foundation; `init`, `doctor` (accurate tier table).
- Blogs/RSS live: real Guardian + Marketing-AI-Institute feeds collected,
  stored, scored, newsletter-rendered; dead sample URLs replaced with verified
  ones (the 404 → junk-sitemap incident is on record, fixed + filtered).
- `collect` twice → 0 dupes; `build` twice → 1 row; demo twice → byte-identical
  files (SHA256 match).
- Grouding/validation pipeline, premailer inlining, dark-mode retention, HTML
  parse checks, stored-JSON revalidation.
- Live API server: `/health`, 401s, `POST /runs`, history, archive, 11KB
  preview, all dashboard pages, feedback roundtrip, iframe detail.
- File delivery + CLI `send`; provider/generic mapping + all tier fallbacks
  (respx); scheduler registration + fault isolation; JSON/text logging shape.
- `docker compose config` validates; Dockerfile import-check passes.

### FIXTURE-TESTED ONLY (shapes mirror docs, not live traffic)
- YouTube Data API mapping/quota accounting/403 handling; Reddit OAuth flow;
  X search mapping + 402 paywall branch; LinkedIn userinfo verify; Instagram
  media mapping + hashtag filter; generic provider (401/non-JSON/row-skips);
  Quora RSS-attempt branch. Fixtures are labeled RECORDED, never presented
  as live responses.

### NEEDS LIVE CREDENTIALS (code-reviewed, graceful today, unproven live)
- YouTube/Reddit/X/LinkedIn/Instagram official calls with real keys; one
  keyed LLM run (Anthropic/OpenAI path executes only with a key);
  SMTP/Resend/webhook actual sends; Docker image build + serve-in-container
  (no engine on this machine); Postgres DSN (code is URL-agnostic, only
  SQLite exercised); Alembic versioned migrations (schema still v1,
  `create_all` covers fresh DBs).

### Known gaps carried forward (no new claims)
- SimHash-8 / cosine-0.22 tuned on one 13-item fixture (parameters exposed).
- Authority table static until feedback accrues; momentum is a recency
  heuristic; stub prose is robotic; `POST /runs` is inline (no queue);
  token auth is single-secret dev-grade; LinkedIn official tier verifies only
  (platform limitation); Quora needs provider/manual, full stop.

**Project complete per the 8-phase plan. Awaiting live keys + a Docker host
for the remaining live proofs — everything else is green and on record.**

## Phase 7 — Hardening + demo + containers (COMPLETE, verified 2026-10-10)

### What was built
- `logging.py`: stdlib JSON-lines (`LOG_FORMAT=json`, ts/level/logger/msg/ctx)
  or human text (`LOG_LEVEL`); no new deps; secrets never logged (counts/tiers
  only). Wired into CLI (global `--log-format/--log-level`), API access-log
  middleware (method/path/status/ms), collector runs, builds, deliveries,
  scheduler outcomes.
- Retry audit: collectors/LLM already had tenacity backoff; Resend + webhook
  now retry transport/5xx 3× before failing (test updated to the new message).
  Rate limits unchanged (per-collector `AsyncRateLimiter` from sources.yaml)
  + new math/unit tests (intervals, unlimited fast path).
- `newsletter-machine run`: full collect→build→deliver via `run_daily`
  (+`--niche`, `--date`, `--since-hours`); `run --demo` seeds 5 labeled
  FIXTURE rows (niche `demo`, `demo-` ids, example.com URLs) and builds +
  file-delivers with the stub — zero keys, zero network, rerun-safe.
- `scheduler.run_daily` gained an optional `niche_id` filter (backward
  compatible). CLI `build` refactored onto shared `build_flow` (same path for
  CLI/scheduler; suite stayed green through the refactor).
- Containers: Dockerfile hardened (tzdata, import smoke check, HEALTHCHECK via
  stdlib urllib, JSON logs), compose `env_file` optional + sane defaults,
  `.dockerignore` added. `docker compose config` validates cleanly.
- Makefile: added `run/demo/collect/build/send/schedule/docker-build/docker-up`.
- Tests: `test_hardening` (6: limiter math, JSON/text logging shape, live
  respx collect×2 idempotency + build×2 single-row/scores, zero-key demo×2).
- README: zero-key demo first, env-var reference table, expanded
  troubleshooting, Phase 6 CLI/API/delivery/scheduler docs.

### Commands run (real output summary)
- `uv run pytest -q` → **123 passed, 3 skipped** (key-gated live tests only).
- `uv run ruff check .` → **All checks passed!**
- `run --demo` (scratch DB, twice): 1st 5 inserted → newsletter #1 + file
  receipt; 2nd 0 inserted / 5 skipped → same newsletter #1. DB: 5 items,
  1 newsletter. Temp files removed after.
- Final `run` (scratch DB, zero keys, JSON logs): ai-tools-marketers +20,
  sustainable-travel +1 → 2 newsletters built → file-delivered; 6 files on
  disk; DB: 21 items, 2× `delivered`, 2× `partial` runs (partial = some
  collectors degraded, documented per-tier). Temp files removed after.
- `docker compose config` → parses + interpolates cleanly. `docker build`
  NOT runnable here (no engine — client-only install); Dockerfile improvements
  are reviewed + import-checked locally, build/serve-in-container unverified.
- `python -c "import newsletter_machine.cli, newsletter_machine.api.main"`
  → OK (mirrors the Dockerfile smoke check).

### Known gaps / honest notes
- **Latent NameError caught by the new test**: `runner.py` used
  `timezone.utc` with only `UTC` imported — every `collect_and_store` call
  should have crashed, yet Phase 6's suite was green. The new
  collect×2 end-to-end test exposed it immediately (fixed: one line). Lesson:
  unit tests mocked around the integration seam; the e2e test is now
  permanent. Ruff did not flag the undefined name either (noted toolchain
  limitation — the e2e test is the backstop).
- Docker image never built here (no daemon); needs `docker build` + `up` +
  `/health` on a Docker host before claiming container-ready.
- Live sends (SMTP/Resend/webhook) still unproven without credentials.
- `POST /runs` still inline (no worker queue) — acceptable for daily cadence.

### Next
Awaiting "continue" → Phase 8 (final audit: full suite + ruff + fixture e2e,
verified-vs-fixture-only-vs-needs-credentials list).

## Phase 6 — Delivery + scheduler + API + dashboard (COMPLETE, verified 2026-10-10)

### What was built
- JSON API (`api/main.py` factory + 6 routers): `/health` open; token auth
  (`X-API-Token`/Bearer/`?token=`, compare_digest) on everything else.
  Niches full CRUD (409 when items block delete); sources read-only status
  (7 collectors, configured vs live tier, credential presence — names only);
  runs list/get + POST trigger (inline `collect_and_store`, 404 on bad niche);
  newsletters list/get + HTML preview from disk (404 when missing);
  feedback POST-JSON + GET-for-email-links (thanks page) + stats endpoint.
- Dashboard (Jinja2 + HTMX polling on the feedback box, plain-POST run
  trigger so it works without JS): home counts, niches editor, sources tier
  table, run history with per-collector stats/errors, newsletter archive +
  iframe preview detail, feedback stats. Same token auth (`?token=` in links).
- `pipeline/deliver.py`: file (receipt + missing-file list), SMTP/STARTTLS,
  Resend, webhook, none — each with config validation raising DeliveryError;
  receipt stamped into `content_json.delivery`, status → delivered.
- `pipeline/build_flow.py`: per-niche build extracted from the CLI so the
  scheduler reuses the exact same path (CLI refactored onto it, tests green).
- `scheduler.py`: `run_daily()` (collect 24h → build → deliver per niche,
  per-niche try/except isolation) + `build_scheduler()` (cron at
  `send_time`/`timezone`, bad time falls back to 07:00).
- CLI: `serve` (uvicorn), `send --newsletter [--method] [--to]`, `schedule`
  (blocking cron); only `run --demo` remains a stub (Phase 7).
- Tests: `test_api` (9: auth matrix, niches CRUD+409, sources tiers, live
  respx run trigger + history, preview incl. 404, feedback POST/GET/stats,
  all dashboard pages + HTMX attr, dashboard form create/delete),
  `test_deliver` (6: file receipt + row status, unknown/missing errors, SMTP
  config-gate + faked send, respx resend/webhook + 500 path, CLI send),
  `test_schedule` (3: cron registration 07:00, bad-time fallback, run_daily
  fault isolation with patched transports). Ruff B008 allowlisted with
  justification (FastAPI Depends pattern).

### Commands run (real output summary)
- `uv run pytest -q` → **117 passed, 3 skipped** (key-gated live tests only).
- `uv run ruff check .` → **All checks passed!**
- Live server (uvicorn :8123, temp DB staged with 6 collected items + 2 built
  newsletters, real output): `/health` → `{"status":"ok"}`; no token → 401;
  `POST /runs` (quora) → 200, 0 inserted, status failed/tier disabled
  (graceful, no crash); `GET /runs` → 3 rows (2 success + 1 API-triggered);
  `GET /newsletters` → both editions; preview → 200, 11KB HTML; dashboard
  home/runs/newsletters/feedback → 200; feedback POST → id 1, stats total 1;
  newsletter detail → 200 with preview iframe. Server stopped, temp files
  removed, dev DB untouched (verified: digest + 2 niches still on disk).
- `send --newsletter` file path covered by CLI test (exit 0 + receipt line).

### Known gaps / honest notes
- `POST /runs` runs collection INLINE (up to a minute behind rate limits) —
  fine for daily use, no worker queue; Phase 7 may add BackgroundTasks.
- Token auth is one shared secret (documented dev-grade, localhost/TLS scope).
- SMTP/Resend/webhook are transport-tested with fakes/respx, NOT live-sent
  (no mail credentials or webhook on this machine).
- Scheduler `run_daily` itself never ran end to end here (would hit live
  collection + delivery); registration + isolation are tested, execution is
  Phase 7's end-to-end territory with `--demo`.
- HTMX loads from CDN (degrades to plain forms offline — trigger is a normal
  POST by design).

### Next
Awaiting "continue" → Phase 7 (hardening: structured logging, idempotency
proof, Dockerfile/compose verification, `run --demo` end-to-end, README
credential polish, Makefile targets).

## Phase 5 — LLM analysis + composer + templates (COMPLETE, verified 2026-10-10)

### What was built
- `llm/schemas.py`: pydantic contract for all 8 analysis sections + coverage
  (tldr 1–5, opportunities ≤10, momentum enum, min-1 source per story).
- `llm/local_stub.py`: deterministic EXTRACTIVE stub (titles, first
  sentences, real "..." spans, reddit/quora "?" titles, templated
  opportunities/creators/action) — obeys grounding rules so one test suite
  covers stub and real LLMs. Empty input → valid light edition.
- `llm/anthropic_client.py` + `openai_client.py`: plain-httpx clients (no SDK
  deps), backoff retries, distinct 401/402/429 errors, fence-stripping JSON
  parse. `llm/prompts.py` holds the grounding system prompt + schema sketch.
  `llm/factory.py` selects by `LLM_PROVIDER` with clear missing-key errors.
- `pipeline/analyze.py`: payload builder (ranked items truncated to 1500
  chars, clusters with deterministic momentum from median member age,
  coverage counts), `ground_analysis` (drops ungrounded stories/trends/
  highlights/questions/creators/opportunities + non-verbatim quotes, returns
  dropped counts), `run_analysis` (3 validation attempts for live clients, 1
  for stub; LLMError on exhaustion).
- `pipeline/compose.py`: content assembly honoring `sections_order`+enabled+
  max_items, subject templating, per-story feedback URLs (real newsletter +
  item ids), diagnostics footer (tiers, errors, dropped-claim counts),
  premailer CSS inlining (graceful without it), dark-mode `@media` kept,
  `persist_rendered` shared by per-niche builds and the combined digest.
- Templates: email-safe 600px table HTML, Markdown, plain text — all sections
  toggleable, empty sections skipped.
- CLI `build`: window → pipeline → analysis → diagnostics (latest Run) →
  files + Newsletter upsert (idempotent per day/niche); `--digest` merges
  niches. Unknown niche / bad date / LLM failure exit 1 with messages.
- Tests: `test_llm_analysis` (10: momentum, fence parsing, stub validity +
  quote-exactness + empty, fabrication drops, flaky-client retry 3×,
  give-up paths, truncation, factory), `test_compose` (5: subject/feedback/
  caps, disabled sections, all formats + inline CSS + dark query, file write
  + row upsert, digest merge), `test_build_cli` (3: files + rebuild
  idempotency, digest regression, unknown niche), `test_live_llm` (1, skips
  without keys).

### Commands run (real output summary)
- `uv run pytest -q` → **101 passed, 3 skipped** (2 live-collector keys +
  1 live-LLM key; everything else fixture/stub, no network).
- `uv run ruff check .` → **All checks passed!**
- `build --since-hours 720` on the dev DB (7 real collected items) → 2
  newsletters (`ai-tools-marketers`, `sustainable-travel`), stub analysis.
- File verification script: both HTML parse clean (balanced-tag check),
  `style="` inlined + `@media` retained, MD has `## TL;DR`, TXT headers
  present (html 9–15KB, md 3–7KB, txt 2.8–6.6KB); both Newsletter rows
  `status=built`; stored `content_json.analysis` revalidates against
  AnalysisResult.
- `build --digest` → combined `digest/newsletter.{html,md,txt}` with stories
  from both niches. (First attempt exposed a REAL bug — `s["key"]` vs stored
  `item_key` KeyError — fixed, regression test added, rebuilt clean.)
- Live LLM: NO key on this machine → `test_live_llm` skips with reason; the
  anthropic/openai paths are code-reviewed + interface-tested, NOT live-proven.

### Known gaps / honest notes
- Stub analysis is extractive/templated ("Ranked #N (score…)", "Create a …
  about …") — correct for tests/demos, obviously robotic next to a real LLM.
  One keyed run is still needed to prove the live path end to end.
- Momentum is a recency heuristic (median member age), not true week-over-week
  trend velocity — labeled as such in stub notes; real momentum needs run
  history comparison (Phase 7 candidate).
- Default model ids (`claude-3-5-haiku-20241022`, `gpt-4o-mini`) are pinned
  known-good values, overridable via env — re-check currency before spending.
- Feedback links are relative `/feedback?...` URLs (API lands in Phase 6).
- Digest re-renders from stored analyses (no re-analysis) — cheap and
  consistent by design.

### Next
Awaiting "continue" → Phase 6 (delivery + scheduler + API + dashboard:
serve /health, trigger runs via API, preview newsletters).

## Phase 4 — Pipeline: normalize, dedupe, scoring, clustering (COMPLETE, verified 2026-10-10)

### What was built
- `pipeline/normalize.py`: `NormalizedDoc` (source-agnostic clean record) +
  `normalize_doc()` (duck-typed over collector Items and DB rows; metrics from
  `.metrics` or `.metrics_json`; canonical fill; language lowercase/default).
- `pipeline/dedupe.py`: canonical-URL exact pass + vendored 64-bit SimHash
  (blake2b word-3-grams, deterministic) with title triple-weighting.
  Threshold 8 was **calibrated, not guessed**: fixture measurements showed the
  true repost twin at 6 and the closest non-dupe pair at 21 (title×3 moved the
  twin from 11; non-dupes stayed ≥21). First wins; removals carry reasons.
- `pipeline/scoring.py`: the spec formula exactly —
  recency (0.5**(age/48h)) + engagement velocity (log1p(total)/sqrt(age+2),
  **min-max normalized per platform** so YouTube views can't drown Reddit
  upvotes; no variance → 0.5) + platform authority base + keyword relevance
  (title×2, related half, exclude-hit → 0.0, no keywords → 0.5) + novelty
  (0.3 if canonical refetched within 7d, else 1.0) + feedback prior
  (up+1/click+0.5/down−1 platform mean → 0.5±0.3; none → 0.5). Weights merge
  `niche.weight_overrides` and renormalize; totals in [0,1]; components stored.
  `persist_scores` upserts one ItemScore row per item.
- `pipeline/cluster.py`: dependency-free TF-IDF (built-in stopwords, title×2
  term boost, smoothed IDF) + single-link union-find at cosine ≥ 0.22; labels
  are top-3 terms; `persist_clusters` stores member DB ids (summaries left for
  the Phase 5 LLM).
- `pipeline/run.py`: `run_pipeline()` orchestration returning a
  PipelineReport (ranked, dedupe detail, clusters, threshold split, write
  counts). Judgment call, documented in code: `above_threshold` requires
  total ≥ min_score AND relevance > 0, so excluded/off-topic heat can't pass
  on virality alone; the full ranked list is always kept for audit.
- Fixture dataset `tests/fixtures/pipeline_items.json`: 13 items (AI-topic
  cluster with a repost twin + cross-platform canonical repost, travel pair,
  stale gem, excluded spam, irrelevant noise) with `age_hours` for
  determinism. Tests: `test_dedupe` (5), `test_scoring` (7, incl. seeded-DB
  novelty/feedback/persist), `test_cluster` (4), `test_pipeline` (1 e2e:
  13→11, ranking, 6 clusters, 11 scores persisted, threshold behavior).

### Commands run (real output summary)
- `uv run pytest -q` → **83 passed, 2 skipped** (same 2 live-key skips; all
  17 Phase-4 tests deterministic, no network).
- `uv run ruff check .` → **All checks passed!** (plus `ruff format` on new files).
- Ranked demo (temp DB seeded from the fixture, `run_pipeline`, real output):
  13 in → 11 unique (removed `blogs:blog1b` simhash≤8, `reddit:dupurl`
  canonical-url); top-3 `youtube:yt1` 0.663 / `reddit:r1` 0.654 / `x:x1`
  0.646 (all recent+relevant); stale gem `blogs:old1` 0.241 last (recency
  decay working); excluded spam `manual:noise1` 0.503 second-to-last on
  relevance 0.0; `above_threshold` (0.3) = 6 relevant items; 6 clusters —
  `[marketing automation chatgpt]` ×5, `[trains slow travel]` ×2, 4 singles;
  11 scores + 6 clusters persisted. Temp DB deleted after.

### Known gaps / honest notes
- SimHash threshold 8 and cluster cosine 0.22 are calibrated on ONE 13-item
  fixture (twin 6 vs closest-non-dupe 21) — reasonable margin, but production
  data will differ; both are parameters (`sim_threshold`, `cluster_threshold`)
  precisely so Phase 7+ can re-tune from real runs. False positives hide
  stories; watch removals in the diagnostics footer.
- Travel items (relevance 0.0) outranked the relevant `blogs:blog1` on
  recency+velocity in the demo — correct per default weights, but niches with
  noisy feeds will want `weight_overrides: {relevance: 0.4}` (supported).
  `blog1` also took novelty 0.3 because its canonical twin `dupurl` sits in
  the DB — arguably correct ("already seen"), worth knowing.
- Authority is a static platform table (honest proxy, documented); feedback
  prior starts neutral until readers vote (Phase 6). No embeddings —
  TF-IDF is the documented choice for this volume; swap point is `cluster.py`.
- No CLI surface for the pipeline yet (`build` arrives in Phase 5 with the
  composer); verification ran `run_pipeline` directly.

### Next
Awaiting "continue" → Phase 5 (LLM analysis JSON + composer + HTML/MD/TXT
templates, stub-tested, one real-LLM run only with a key).

## Phase 3 — Restricted platforms: tier system (COMPLETE, verified 2026-10-10)

### What was built
- `collectors/providers/` — one pluggable interface: `DataProvider.fetch`
  + `ProviderError`, `GenericHTTPProvider` (POSTs {platform, queries, since,
  limit} to `PROVIDER_BASE_URL`, maps documented `{"items"}` schema, skips
  bad rows, raises on 401/402/429/5xx/non-JSON), factory `get_provider()`
  (None when unconfigured) + `manual_hint()`. Nothing scrapes; it maps lawful
  third-party JSON only.
- `collectors/x_twitter.py` — X API v2 `tweets/search/recent` (queries +
  `from:` accounts, metrics incl. views, per-query dedupe). 402 = paywall
  (stops querying, falls through), 401/403 and 429 recorded distinctly.
  Chain: official_api → provider → manual hint. No token → honest `disabled`.
- `collectors/linkedin.py` — built around the documented limitation that the
  official API has NO post search: verifies `LINKEDIN_ACCESS_TOKEN` via
  OpenID `/v2/userinfo` (quota 1, valid/invalid recorded), then falls to
  provider → manual. `tier_used` is `official_api` only when the token was
  actually exercised, else `disabled`.
- `collectors/instagram.py` — Graph API own-account media (`/{id}/media`,
  versioned path), client-side caption filtering by niche hashtags/keywords,
  metrics + image URLs. Hashtag search deliberately NOT faked (needs approved
  app — documented). Chain: official_api → provider → manual.
- `collectors/quora.py` — ground truth first: live check 2026-10-10 showed
  topic pages HTTP 403 to bots, so default chain is provider → manual with a
  plain-English "no official API / no public RSS" error. `tier: rss` remains
  supported: tries `{topic}/rss` once per topic and records the expected
  failure instead of crashing.
- `runner.build_collector` now passes `tier:` from `sources.yaml` as each
  collector's preferred tier (config actually drives behavior); all collectors
  are `None`-niche safe (contract test still passes).
- `sources.yaml`: preferred-tier semantics documented in header;
  `credential_env_vars` for the 4 collectors now include provider vars.
- Tests: 5 new files, all fixture-based (respx): `test_providers` (7:
  mapping, 401/non-JSON/missing-URL errors, factory), `test_x` (5: official
  mapping + dedupe, 402→provider fallback, disabled paths, tier_status),
  `test_linkedin` (5: verify-then-explain, bad token, provider fallback),
  `test_instagram` (5: hashtag filter, 401, missing-creds hint),
  `test_quora` (5: default degradation, provider, explicit-rss 403).

### Commands run (real output summary)
- `uv run pytest -q` → **67 passed, 2 skipped** (same 2 live-key skips as
  Phase 2; all Phase-3 tests use RECORDED FIXTURES in `tests/fixtures/`).
- `uv run ruff check .` → **All checks passed!**
- Live ground-truth checks (single polite requests): Quora topic + `/rss`
  → HTTP 403 (no public feed — baked into code/docs as verified fact).
- `collect --platforms x,linkedin,instagram,quora` (temp DB, zero keys) →
  exit 0, 0 items, per-collector honest errors (X paywall note, LinkedIn
  missing-token note, Instagram own-account note, Quora no-API note), Run
  status `failed` with errors recorded — degradation proven, no crash.
- `collect --platforms quora --manual-file tmp_quora.csv` (temp DB) → quora
  collector 0 items + errors, manual tier +1 inserted — the documented gap
  fill works end to end.
- `doctor` → exit 0; all 7 collectors show per-tier availability (token
  missing / provider unset / manual always available); secrets all `not set`.

### Known gaps / honest notes
- X/LinkedIn/Instagram official paths and the generic provider are
  **fixture-tested only** (no keys/provider on this machine). Fixtures mirror
  documented API shapes (X v2 search, Graph media, OpenID userinfo) but are
  not live responses — set keys and run `collect --platforms x` etc. to verify
  live; 402/403/429 handling is code-reviewed, not live-proven.
- LinkedIn official tier can only ever verify + explain (platform limitation,
  not a bug). Instagram hashtag monitoring needs an approved Meta app or a
  provider. Quora needs a provider or manual import, full stop.
- No caching layer yet (Phase 7). `tier_used` for LinkedIn-without-token is
  `disabled` (fixed during verification — was briefly `official_api`).

### Next
Awaiting "continue" → Phase 4 (normalize, dedupe, scoring, clustering with a
seeded fixture dataset and ranked output).

## Phase 2 — Official/free-access collectors (COMPLETE, verified 2026-10-10)

### What was built
- `collectors/http.py`: shared polite HTTP — per-platform `AsyncRateLimiter`
  (from `sources.yaml`), tenacity 3-attempt exponential backoff on 429/5xx/
  transport errors, honest `User-Agent` client factory.
- `pipeline/normalize.py` (Phase 2 slice): `canonicalize_url` (tracking-param
  stripping, fragment/port handling, query sort) + `normalize_text`. Pure,
  tested; Phase 4 extends it.
- `collectors/blogs.py` (tier `rss`): multi-feed fetch via httpx + feedparser,
  `since` filtering, trafilatura full-text upgrade for short summaries
  (budgeted, best-effort), media extraction, sitemap fallback with
  asset-extension filtering + sitemap-index following. Per-feed errors recorded.
- `collectors/youtube.py`: Data API v3 `search.list` (queries + `UC…`
  channelIds) then `videos.list` stats batches; quota estimates reported
  (~100/search + 1/videos call). No key + `UC…` channels → public channel-RSS
  fallback (`tier_used="rss"`); no key otherwise → honest `disabled`. No
  transcripts (API has none; descriptions stored, never fabricated).
- `collectors/reddit.py`: script-app OAuth (`access_token` → hot + top/week per
  sub + keyword search), metrics {upvotes, ratio, comments}. No creds →
  public `hot.json` fallback (`tier_used="public_json"`, no search). 401/403/
  429 recorded, never raised.
- `collectors/manual_import.py`: CSV (requires `url` header; per-row platform,
  metric columns, sha256 `external_id` fallback) / JSON (list or
  `{"items"}`) / TXT URL-list (`#` comments, blank lines skipped) → collector
  `Item`s. Clear `FileNotFoundError`/`ValueError` messages.
- `collectors/runner.py`: `run_collectors` (enabled-only, `--platforms`
  filter, per-collector caps, never crashes) + `upsert_items` (idempotent on
  `(platform, external_id)`) + `collect_and_store` (per-niche `Run` rows with
  stats/errors, status success|partial|failed).
- CLI `collect` fully working: `--niche/--platforms/--limit/--since-hours/
  --manual-file/--manual-platform`, rich per-collector table, totals.
- Sample configs fixed with **verified-live** feeds (old Phase 1 URLs 404'd):
  Marketing AI Institute `.../blog/rss.xml` + Guardian `.../travel/rss`
  (both HTTP 200, checked 2026-10-10). responsibletravel.com has no RSS —
  documented in config instead of a dead URL.
- Tests: 6 new files, all fixture-based except 3 clearly-marked live smokes:
  `test_normalize` (6), `test_blogs` (5, respx), `test_youtube` (4, respx),
  `test_reddit` (4, respx), `test_manual_import` (6), `test_runner` (2),
  `test_live_smoke` (3: YouTube/Reddit SKIP without keys, blogs RSS live PASS).

### Commands run (real output summary)
- `uv run pytest -q` → **40 passed, 2 skipped** (skips: live YouTube/Reddit —
  `YOUTUBE_API_KEY` / `REDDIT_CLIENT_ID+SECRET` not set; all other tests use
  RECORDED FIXTURES in `tests/fixtures/`).
- `uv run pytest tests/test_live_smoke.py -v` → 1 passed (live Guardian/MI
  RSS over real network), 2 skipped with reasons printed.
- `uv run ruff check .` → **All checks passed!** (plus `ruff format` on new
  files; ~60 auto-fixed findings, rest hand-fixed).
- `uv run newsletter-machine collect --platforms blogs --limit 5 --since-hours 168`
  (after `init --force` on a fresh DB) → run 1+2: **7 inserted, 0 dup**
  (2× Marketing AI Institute + 5× Guardian, all Oct 6–10 2026, zero errors).
  Re-run → **0 inserted, 7 skipped** (idempotent; verified in DB: 7 rows).
- `collect --niche ai-tools-marketers --platforms manual --manual-file
  tests/fixtures/manual.csv` (temp DB) → 2 loaded, 2 inserted, tier `manual`.
- `uv run newsletter-machine doctor` → exit 0; blogs=rss ready; youtube/reddit
  correctly show missing keys + fallback notes; X/LinkedIn/Instagram/Quora
  still Phase-3 stubs; all secrets `not set`.

### Known gaps / honest notes
- First live run exposed the Phase 1 sample feed 404 → sitemap fallback stored
  5 junk asset URLs (images/SVGs) before filtering existed. Fixed: sample URLs
  replaced with verified feeds, sitemap now filters assets + follows indexes;
  junk rows deleted via DB reset. Lesson recorded, not hidden.
- YouTube/Reddit live paths are **fixture-tested only** (no keys on this
  machine); respx fixtures mirror documented API shapes but are not live
  responses. Run `pytest tests/test_live_smoke.py -v` with keys to verify live.
- Guardian travel feed is general travel, not strictly "sustainable" — best
  verified free option found; niche relevance scoring (Phase 4) will rank
  within it. Reddit public fallback has no keyword search (needs OAuth).
- X/LinkedIn/Instagram/Quora remain skeletons (Phase 3). No transcript
  fetching (by design). No caching layer yet beyond per-run budgets.

### Next
Awaiting "continue" → Phase 3 (X/LinkedIn/Instagram/Quora tier system +
provider interface, graceful degradation, tier docs).

## Phase 1 — Foundation (COMPLETE, verified 2026-10-10)

### What was built
- Full repo scaffold exactly per spec (`newsletter_machine/`, `config/`, `tests/`,
  `output/newsletters/`, `pyproject.toml`, `Dockerfile`, `docker-compose.yml`,
  `Makefile`, `alembic.ini`, `.env.example`, `README.md`).
- `config.py`: pydantic-settings (`Settings`, `.env` support) + YAML loaders
  (`load_niches`, `load_sources`, `load_newsletter`) with typed models
  (`NicheConfig`, `PlatformTargets`, `SourcesConfig`, `NewsletterConfig`).
- `db/models.py`: SQLAlchemy 2.x models — Niche, Source, Item (unique
  `(platform, external_id)`), ItemScore, Cluster, Run, Newsletter, Feedback,
  Setting. `db/session.py`: engine/session/init_db/session_scope (SQLite
  default, Postgres-compatible URL).
- Alembic `env.py` + ini wired to `Base.metadata` (fresh DBs via `create_all`;
  revisions to be added as schema evolves).
- Collector contract (`collectors/base.py`: `Item`, `CollectorResult`,
  `BaseCollector.collect` never-crash rule) + `registry.py` discovery +
  skeleton adapters for youtube/reddit/x/linkedin/instagram/quora/blogs +
  `providers/base.py` + `manual_import.py` placeholder.
- Pipeline/LLM/template/API/scheduler placeholders so imports are stable;
  real `/health` endpoint working.
- CLI (`cli.py`): `init` (copies `.env.example`→`.env`, creates DB, upserts
  niches) and `doctor` (python/config/DB/collector-tier/env table, secrets
  presence-only) fully working; `collect|build|send|run|serve|schedule` are
  honest stubs that exit 0 with "lands in a later phase".
- Sample configs for 2 niches (`ai-tools-marketers`, `sustainable-travel`),
  `sources.yaml` (7 collectors with tiers), `newsletter.yaml`
  (9 sections, file delivery).
- Tests: `test_config` (4), `test_db` (3: unique constraint, newsletter
  upsert pattern, run/feedback roundtrip), `test_cli_api` (4: help, doctor
  without keys, /health, collector never-crash). All fixture-based, no network.

### Commands run (real output summary)
- `uv sync --group dev` → SUCCESS (installed fastapi, sqlalchemy, typer, pytest, ruff, …).
- `uv run pytest -q` → **11 passed** in ~3.8s (1 pre-existing
  StarletteDeprecationWarning about httpx TestClient, harmless).
- `uv run ruff check .` → **All checks passed!** (after fixing 17 findings:
  E501 line-length splits, B904 `raise … from`, F841/B007 cleanups, I001 import
  sort, UP037/UP017 modernizations).
- `uv run newsletter-machine init` → SUCCESS:
  `Created .env from .env.example`, `Database ready: sqlite:///./newsletter_machine.db`,
  `Synced 2 niche(s) into the database.`
- `uv run newsletter-machine doctor` → SUCCESS, exit 0. Table shows:
  python 3.13.14; 3 YAML files OK; niches OK (2); sources OK (7);
  database OK (sqlite); blogs=rss ready-Phase-2; youtube/reddit/x/linkedin/
  instagram correctly report missing keys; quora=manual/no official API;
  all 10 env vars honestly `not set` (zero-keys machine).

### Known gaps (by design — later phases)
- Collectors are skeletons returning `tier_used="disabled"` + honest error
  strings; no live collection yet (Phase 2: blogs/YouTube/Reddit/manual;
  Phase 3: X/LinkedIn/Instagram/Quora tiers + provider interface).
- Pipeline (normalize/dedupe/scoring/cluster), LLM analysis, composer
  templates, delivery, scheduler, dashboard CRUD are placeholders.
- Alembic has no versioned revisions yet (create_all covers Phase 1).
- `doctor` env section reports process env only (reads `.env` via settings for
  DB/paths; secret presence via `os.getenv` — `.env` file alone doesn't set
  `os.environ` unless exported; documented behavior, not a bug for Phase 1).
- Docker image not built/tested yet (Phase 7 hardening).

### Next
Awaiting "continue" → Phase 2 (working blogs/RSS, YouTube, Reddit, manual
import with fixture tests + live smoke where keys exist).
