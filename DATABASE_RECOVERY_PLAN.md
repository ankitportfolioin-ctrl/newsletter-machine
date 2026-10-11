# Database Recovery Plan — Newsletter Machine (Production)

> **Status:** PROPOSED — awaiting explicit owner approval. Nothing in this plan
> has been executed against production. No SQL has been run, no data modified,
> no code deployed as part of this task. The deliverables are this plan plus
> two inert SQL files (not executed by any build).

## 0. Boundary and approval gate

- **Do NOT run anything in this plan without explicit owner approval.**
- Approval covers exactly: (1) taking the backups in §4, (2) running
  `server/supabase-migration-safe.sql` once in the Supabase SQL Editor,
  (3) running `server/supabase-verify.sql` before/after.
- Out of scope: assigning legacy rows to users, disabling RLS, dropping
  tables, touching `auth.*`, touching frontend/Vercel.

---

## 1. Phase A — Inspection findings

### 1.1 What the deployed backend expects (authoritative)

Source: `server/src/` at local master `e65f900` (see §1.4 for deployed==local
reasoning). **Every** table access goes through `supabaseAdmin`
(service_role key); `src/config/database.ts` (pg Pool) is dead code imported
by nothing; `routes/legal.ts` is static (no DB use).

| Table | Columns (all required) | Key constraints |
|---|---|---|
| `niches` | `id` UUID PK default `gen_random_uuid()`, `user_id` UUID FK→`auth.users(id)` ON DELETE CASCADE (**nullable**), `name` VARCHAR(500) NOT NULL, `keywords`/`subreddits`/`blog_feeds`/`include_terms`/`exclude_terms` TEXT[] default `'{}'`, `enabled` BOOLEAN default true, `created_at`/`updated_at` TIMESTAMP default NOW() | PK on `id` |
| `sources` | above + `platform` VARCHAR(50) NOT NULL, `status` default `'not_configured'`, `credentials` JSONB default `'{}'`, `last_checked` TIMESTAMP, `items_collected` INTEGER default 0 | PK + **UNIQUE(`user_id`,`platform`)** (upsert target) |
| `collected_items` | `id` UUID PK, `niche_id` UUID FK→`niches(id)` CASCADE, `platform` VARCHAR(50) NOT NULL, `title` TEXT NOT NULL, `url` TEXT NOT NULL, `author` VARCHAR(255), `score` INTEGER default 0, `excerpt` TEXT, `metadata` JSONB default `'{}'`, `collected_at` default NOW() | PK |
| `runs` | `id` UUID PK, `user_id` FK, `niche_id` UUID FK→`niches(id)` CASCADE, `status` default `'pending'`, `started_at` default NOW(), `completed_at`, `stats` JSONB default `'{}'`, `errors` TEXT[] default `'{}'`, `created_at` | PK |
| `newsletters` | `id` UUID PK, `user_id` FK, `niche_id` FK, `run_id` UUID FK→`runs(id)` CASCADE, `date` DATE NOT NULL, `subject` TEXT NOT NULL, `preheader` TEXT, `content` JSONB NOT NULL, `created_at` | PK |
| `feedback` | `id` UUID PK, `user_id` FK, `newsletter_id` UUID FK→`newsletters(id)` CASCADE, `story_id` VARCHAR(255) NOT NULL, `vote` VARCHAR(10) CHECK (`up`/`down`) | PK + **UNIQUE(`user_id`,`newsletter_id`,`story_id`)** (upsert target) |

Indexes required: `idx_niches_user_id`, `idx_collected_items_niche_id`,
`idx_collected_items_url`, `idx_runs_user_id`, `idx_newsletters_user_id`,
`idx_feedback_user_id`.

Hidden hard requirements (would break silently if missing):
- FK `runs.niche_id → niches.id` and `newsletters.niche_id → niches.id` must
  exist — `GET /runs` and `GET /newsletters` use PostgREST embedded joins
  (`select(*, niches(name))`), which fail without a detectable FK.
- `user_id` is **nullable** in every table — the app always writes it, but
  nullability means unowned rows are representable and simply invisible to
  per-user queries. The migration relies on this (no fake ownership needed).

### 1.2 What production actually has (probed via REST + OpenAPI, read-only)

| Table | Actual columns | Rows (observed) |
|---|---|---|
| `niches` | `id` varchar, `name`, `description` text, `config_json` json, `created_at` timestamptz. **No `user_id`.** | **2** (`Content-Range: 0-0/2`) |
| `sources` | `id` int4, `platform`, `tier`, `enabled`, `config_json`. No `user_id`. | unknown (count probes flaky — see §1.5) |
| `runs` | `id` int4, `niche_id` varchar, `status`, `started_at`, `finished_at`, `stats_json`, `errors_json`. No `user_id`. | unknown |
| `newsletters` | `id` int4, `date` varchar, `niche_id` varchar, `subject`, `html/md/txt_path`, `content_json`, `status`, `created_at`. No `user_id`. | unknown |
| `feedback` | `id` int4, `newsletter_id` int4, `item_id` int4, `signal` varchar. No `user_id`. | unknown |
| `items`, `clusters`, `settings`, `item_scores` | old-schema only, no counterpart in backend code | unknown |
| `collected_items` | **missing entirely** | n/a |

Consequence: every `.eq('user_id', …)` becomes PostgREST 400 → backend
catch → HTTP 500 on all data endpoints. Verified live (`GET /api/niches`
→ 500 with valid token; 401 without).

### 1.3 Why the existing `server/supabase-migration.sql` is UNSAFE (superseded)

- `DROP TABLE IF EXISTS … CASCADE` on **10 tables**, deleting all rows —
  including the 2 legacy niche rows — with only a "back up anything you
  need" comment. Violates the no-drop rule.
- `CREATE TABLE` (not `IF NOT EXISTS`) → **not rerunnable**; second run hard-fails.
- Drops `items`, `clusters`, `settings`, `item_scores`, which the app never
  uses — destruction with zero benefit.
- No ownership handling, no RLS handling, no verification, no rollback path.
- A `⚠️ SUPERSEDED` header has been added to that file. **Do not run it.**
  Use `server/supabase-migration-safe.sql`.

### 1.4 Deployed-vs-local consistency

- Render builds branch `master` (`rootDir: server`, `npm install --include=dev
  && npm run build`, `npm start`). Local master `e65f900` is fully pushed;
  no uncommitted backend changes exist (workspace dirt is limited to
  pre-existing `.env`/`.gitignore` states and QA artifacts — none affect the
  build). Render uptime observed during QA aligns with an `e65f900` redeploy.
- Residual uncertainty (stated, not assumed): the exact running bundle was
  not fingerprinted. The schema expectations above depend only on table/column
  usage, which has not changed in any recent commit (recent backend commits
  touched tsconfig, deps, auth null-checks, OpenRouter client, init hardening
  — none alter table usage).
- ⚠️ **Behavior change already live via `e65f900`:** `initializeDatabase()`
  now throws when the `exec_sql` RPC is missing/unusable, which crashes boot
  (`process.exit(1)`) instead of serving 500s. Until the migration creates
  `exec_sql`, expect Render **restart-loop log entries with the explicit
  message** `DB init failed at "…": … Run server/supabase-migration.sql…`.
  (Note: the message names the old file; the correct file is
  `supabase-migration-safe.sql` — the log text will be corrected in a
  follow-up; it does not affect function.) This fail-fast is working as
  designed — endpoints were 500ing either way — and resolves itself on the
  first boot after migration.

### 1.5 Known unknowns (handled by the plan, not assumed away)

- Row counts for tables other than `niches` could not be established reliably
  remotely (count probes returned inconsistent 404/206). The pre-migration
  checklist (§5) requires the owner to record them from the SQL Editor.
- Production RLS enablement/policies are unknown (no RLS SQL exists in the
  repo; only aspirational docs). The migration is RLS-neutral (§3.4); §6 Q8
  inspects actual state. The backend uses service_role, which bypasses RLS,
  so the app works under any RLS posture.
- Whether `exec_sql` RPC already exists is unknown. The safe migration uses
  `CREATE OR REPLACE` (works in both cases); the hardened init reports either
  way.

---

## 2. Phase B — Safe migration design (`supabase-migration-safe.sql`)

**Core decision: archive-by-rename, never drop.** Legacy tables
`niches|sources|runs|newsletters|feedback` → `legacy_*`. All rows preserved,
restorable by a single rename. Old-only tables (`items`, `clusters`,
`settings`, `item_scores`) are left completely untouched.

| Design point | How |
|---|---|
| Zero data loss | No `DROP`/`TRUNCATE`/`DELETE` in the file (verified: 0 occurrences). |
| Rerunnable | Rename guarded by `to_regclass` presence checks **plus** a `user_id`-column check (only old-schema tables are archived; a correct table is never renamed). `CREATE TABLE/INDEX IF NOT EXISTS`, `CREATE OR REPLACE FUNCTION`. Second run is a no-op. |
| No fake ownership | `user_id` stays NULLABLE per backend schema; legacy rows remain in `legacy_*` with no owner. New rows always carry the real authenticated id (middleware). Legacy rows are invisible to per-user queries — correct, not guessed. |
| Type conflicts resolved, not forced | Legacy PKs (`varchar`/`int4`) can never satisfy the UUID PK + `gen_random_uuid()` default + FK chains; in-place ALTER would be high-risk. Fresh tables avoid the entire class. |
| FKs/indexes/upserts | Created exactly per §1.1, including the FKs behind the `niches(name)` embeds and both UNIQUE upsert targets. |
| RLS | Untouched — no `ENABLE/DISABLE/POLICY` statements. Service_role bypass means app behavior is identical under any posture. Optional hardening is a separate, explicitly-approved step (see §6). |
| `exec_sql` helper | `CREATE OR REPLACE`, `SECURITY DEFINER`, revoked from `PUBLIC`/`anon`/`authenticated`, granted to `service_role` only. Required: the hardened boot init calls it. Without this section the backend keeps crash-looping (§1.4). |
| Pre-states handled | (a) Current prod (old tables, no legacy_*): rename + create. (b) Already-migrated-via-drop: renames skip, creates fill gaps. (c) Rerun: full no-op. (d) New-schema tables pre-existing: `user_id` check prevents renaming them. |
| Legacy data review | The 2 `legacy_niches` rows (and any other legacy rows) remain queryable for manual review; mapping them into new tables is a human decision, not part of this migration. |

---

## 3. Phase C — Backup and recovery

### 3.1 Tables and records at risk

Everything is **preserved** by design, but the blast radius if the wrong file
(the superseded drop migration) were run instead: all rows in `niches` (2
confirmed), `sources`, `runs`, `newsletters`, `feedback`, `items`,
`clusters`, `settings`, `item_scores`, plus dependent sequences/defaults via
CASCADE. Record exact counts in the pre-migration checklist before running.

### 3.2 How to take a verified backup

1. **Supabase automatic backups:** Dashboard → Database → Backups. Confirm a
   recent backup exists and note its timestamp (retention/PITR depends on
   plan: Free = daily snapshots; Pro/Team = point-in-time recovery — verify
   against your plan's docs, do not assume).
2. **Manual row export (cheap, exact):** Table Editor → each of the 9 tables
   → `···` → Export to CSV. With tiny tables this is a complete, human-
   verifiable backup. Store the CSVs outside Supabase.
3. **Full logical backup (recommended):** Dashboard → Connect → find the
   Postgres connection string, then from a trusted machine:
   `pg_dump "<CONNECTION_STRING>" -F c -f newsletter-machine-backup.dump`
   (connection string contains the DB password — never paste it into chat,
   tickets, or the repo).
4. **Record counts:** run §1–§3 of `server/supabase-verify.sql` and save the
   output as the baseline.

### 3.3 How to verify the backup can be restored

- CSVs: open and spot-check row counts match the baseline; confirm the 2
  niche rows are present with names intact.
- Dump file: `pg_restore --list newsletter-machine-backup.dump` must parse
  without errors (proves structural validity without touching prod).
- Full restore rehearsal: only into a **separate empty Supabase project**,
  never into production.

### 3.4 Rollback (exact SQL, run only if directed post-approval)

Because nothing was dropped, rollback is rename-back + drop-new:

```sql
-- 1. Remove the new empty (or post-migration) tables
DROP TABLE IF EXISTS feedback, newsletters, runs, collected_items, sources, niches;
-- 2. Restore originals
ALTER TABLE IF EXISTS legacy_niches      RENAME TO niches;
ALTER TABLE IF EXISTS legacy_sources     RENAME TO sources;
ALTER TABLE IF EXISTS legacy_runs        RENAME TO runs;
ALTER TABLE IF EXISTS legacy_newsletters RENAME TO newsletters;
ALTER TABLE IF EXISTS legacy_feedback    RENAME TO feedback;
-- 3. Restart the backend (Render → Manual Deploy / Restart).
```

### 3.5 Rollback limitations / irreversible changes

- **Nothing in the safe migration is irreversible.** No rows are deleted.
- Caveat: rows created in the NEW tables after migration (real user niches,
  runs, etc.) would be destroyed by step 1 of the rollback. Export them first
  if rollback is ever needed after go-live.
- `exec_sql` creation persists after rollback (harmless; locked to
  service_role; required by current backend boot anyway).
- The superseded drop migration, if ever run, is NOT recoverable except from
  backup — one more reason it is marked do-not-run.

---

## 4. Phase D — Execution

### 4.1 Pre-migration checklist (all boxes required before Run)

- [ ] Owner approval for this exact plan recorded (who + when).
- [ ] Supabase automatic backup confirmed (timestamp noted: __________).
- [ ] CSV exports saved for all 9 tables (location noted: __________).
- [ ] `pg_dump` file created and `pg_restore --list` parses clean.
- [ ] Baseline recorded: `server/supabase-verify.sql` §1–§3 output saved.
- [ ] Confirmed the file to run is `server/supabase-migration-safe.sql`
      (NOT `supabase-migration.sql`, which is marked superseded).
- [ ] pgcrypto precondition will be checked by the script (§0); note
      Database → Extensions fallback if it ever fails.
- [ ] Maintenance understanding: endpoints already 500; no user-facing
      downtime is introduced by the migration itself (DDL takes seconds).

### 4.2 Execution steps

1. Supabase Dashboard → SQL Editor → **New query**.
2. Paste the full contents of `server/supabase-migration-safe.sql`.
3. **Run.** Expected: a series of `NOTICE: archived: … → legacy_…` (or
   `skip archive: …` on rerun), then `migration-safe complete`.
4. On ANY `ERROR`: stop, copy the full message, do not retry blindly —
   every step is guarded, so a clean rerun after fixing the cause is safe.
5. Wait ~60s for PostgREST schema-cache reload.
6. Render → observe deploy logs: boot should log
   `✅ Supabase database initialized` / `🚀 Server running` (no more
   `DB init failed`). Restart the service manually if it settled into a
   stopped state.

### 4.3 Post-migration verification checklist

- [ ] `server/supabase-verify.sql` §1: 6 new tables present; 5 `legacy_*`
      present (absent only if the drop path was used before — then note it).
- [ ] §3 counts: new tables start at 0 rows; `legacy_niches` = 2 (baseline).
- [ ] §4: every new table has `user_id` UUID; `collected_items` exists with
      `niche_id`/`url`/`title`.
- [ ] §5–§7: 6 indexes, 2 UNIQUE constraints, FK chains incl.
      `runs→niches`, `newsletters→niches`, `newsletters→runs` all present.
- [ ] §8–§9: RLS state recorded (informational); `exec_sql` executable by
      `service_role` only.
- [ ] `GET /health` → `database.status: "healthy"`.
- [ ] Authenticated `GET /api/niches` → **200** `[]` (not 500) — the P0 signal.
- [ ] Product E2E: create niche → 201 → appears in list → persists after
      refresh; trigger run → 202; run history shows it; newsletter +
      feedback paths exercised in the follow-up QA pass.
- [ ] File the verify outputs + migration notices with this plan.

### 4.4 Notes that are not blockers (do not conflate)

- Frontend production bundle is behind (`index-D5pYdIWQ.js` = `96c631c`):
  the AuthCallback OTP fix (`f33106a`) needs promotion, and Supabase
  Site URL/redirects still need setting. Independent of the DB work.
- `OPENROUTER_API_KEY` on Render is unverified — newsletter *generation*
  (not collection/storage) needs it. Independent.
- Optional follow-up hardening (NOT in this migration, needs its own
  approval): `ENABLE ROW LEVEL SECURITY` on the six new tables. Safe
  because service_role bypasses RLS and the frontend never queries tables
  directly — but it changes posture, so it is deliberately excluded here.

---

## 5. What approval is being asked for

1. To back up per §3.2 and record baselines.
2. To run `server/supabase-migration-safe.sql` exactly once in the Supabase
   SQL Editor, with `server/supabase-verify.sql` before and after.
3. To treat §4.3 as the acceptance criteria, with rollback (§3.4) authorized
   only if verification fails and after new-table rows (if any) are exported.

**Explicitly not approved by this plan:** running the superseded drop
migration, assigning legacy rows to any user, changing RLS, touching
`auth.*`, editing backend/frontend code, or deploying anything.
