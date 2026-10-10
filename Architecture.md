&#x20;┌────────────── CONFIG (niches.yaml, sources.yaml, .env) ──────────────┐

&#x20;│                                                                       │

&#x20;▼                                                                       │

SCHEDULER (daily) ─► COLLECTOR LAYER (one adapter per platform)          │

&#x20;                     YouTube │ Reddit │ X │ LinkedIn │ Instagram │      │

&#x20;                     Quora │ Blogs/RSS                                  │

&#x20;                        │  each adapter tries: official API → RSS →     │

&#x20;                        │  pluggable 3rd-party provider → manual import │

&#x20;                        ▼                                               │

&#x20;                 NORMALIZER (common Item schema)                        │

&#x20;                        ▼                                               │

&#x20;                 DEDUPE (canonical URL + near-duplicate hash)           │

&#x20;                        ▼                                               │

&#x20;                 SCORER (recency, engagement velocity,                  │

&#x20;                         source authority, niche relevance)             │

&#x20;                        ▼                                               │

&#x20;                 CLUSTERER (group items into topics/trends)             │

&#x20;                        ▼                                               │

&#x20;                 LLM ANALYST (summaries, insights, "why it matters",    │

&#x20;                              content ideas) ── provider-agnostic       │

&#x20;                        ▼                                               │

&#x20;                 NEWSLETTER COMPOSER (Jinja2 → HTML / MD / plain text)  │

&#x20;                        ▼                                               │

&#x20;                 DELIVERY (save to disk, SMTP/Resend, optional webhook) │

&#x20;                        ▼                                               │

&#x20;                 STORAGE (SQLite via SQLAlchemy) + RUN LOGS ◄───────────┘

&#x20;                        ▲

&#x20;       FASTAPI + minimal dashboard (niches, sources, runs, preview, feedback)

