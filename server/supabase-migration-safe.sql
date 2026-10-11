-- ============================================================================
-- Newsletter Machine — SAFE production schema migration (data-preserving)
-- ============================================================================
-- Run in: Supabase Dashboard → SQL Editor → New query → paste → Run
--
-- Strategy: ARCHIVE-BY-RENAME, never DROP. Legacy tables are renamed to
--   legacy_* (all rows preserved, restorable). New tables are created fresh
--   with the exact schema in server/src/config/supabase.ts.
--
-- Properties:
--   * ZERO data loss by design (no DROP / TRUNCATE / DELETE anywhere).
--   * Rerunnable: every step is guarded (IF NOT EXISTS / to_regclass).
--     Safe to run twice; second run is a no-op.
--   * No fake ownership: legacy rows keep user_id-less shape in legacy_*
--     tables. New user_id columns are NULLABLE; the backend always writes
--     the real authenticated user id. Nothing is assigned to an arbitrary user.
--   * RLS deny-by-default on the six new tables (ENABLE, zero policies);
--     legacy tables' posture untouched. service_role bypasses RLS, so the
--     backend is unaffected; anon/authenticated get no direct table access.
--   * Also repairs a "half-migrated" state: if new tables already exist,
--     only the missing pieces are created.
--
-- Preconditions: pgcrypto extension (preinstalled on Supabase; checked below).
-- Expected runtime: seconds. No downtime needed, but the backend should be
--   restarted after (Render redeploys/restarts pick up the schema; PostgREST
--   reloads its schema cache automatically within ~1 minute).
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 0. Precondition: pgcrypto for gen_random_uuid()
-- ----------------------------------------------------------------------------
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'pgcrypto') THEN
    RAISE EXCEPTION 'Precondition failed: pgcrypto extension is missing. Install it (Supabase: Database → Extensions) and re-run.';
  END IF;
END
$$;

-- ----------------------------------------------------------------------------
-- 1. Archive legacy tables by rename (rows preserved, fully reversible)
--    Skips when: table absent (already migrated via drop path), or already
--    archived (rerun). Old-only tables (items, clusters, settings,
--    item_scores) are deliberately left untouched.
-- ----------------------------------------------------------------------------
DO $$
BEGIN
  IF to_regclass('public.niches') IS NOT NULL
     AND to_regclass('public.legacy_niches') IS NULL
     AND NOT EXISTS (SELECT 1 FROM information_schema.columns
                     WHERE table_schema = 'public' AND table_name = 'niches'
                     AND column_name = 'user_id') THEN
    ALTER TABLE public.niches RENAME TO legacy_niches;
    RAISE NOTICE 'archived: niches -> legacy_niches';
  ELSE
    RAISE NOTICE 'skip archive: niches (absent or already archived)';
  END IF;

  IF to_regclass('public.sources') IS NOT NULL
     AND to_regclass('public.legacy_sources') IS NULL
     AND NOT EXISTS (SELECT 1 FROM information_schema.columns
                     WHERE table_schema = 'public' AND table_name = 'sources'
                     AND column_name = 'user_id') THEN
    ALTER TABLE public.sources RENAME TO legacy_sources;
    RAISE NOTICE 'archived: sources -> legacy_sources';
  ELSE
    RAISE NOTICE 'skip archive: sources (absent or already archived)';
  END IF;

  IF to_regclass('public.runs') IS NOT NULL
     AND to_regclass('public.legacy_runs') IS NULL
     AND NOT EXISTS (SELECT 1 FROM information_schema.columns
                     WHERE table_schema = 'public' AND table_name = 'runs'
                     AND column_name = 'user_id') THEN
    ALTER TABLE public.runs RENAME TO legacy_runs;
    RAISE NOTICE 'archived: runs -> legacy_runs';
  ELSE
    RAISE NOTICE 'skip archive: runs (absent or already archived)';
  END IF;

  IF to_regclass('public.newsletters') IS NOT NULL
     AND to_regclass('public.legacy_newsletters') IS NULL
     AND NOT EXISTS (SELECT 1 FROM information_schema.columns
                     WHERE table_schema = 'public' AND table_name = 'newsletters'
                     AND column_name = 'user_id') THEN
    ALTER TABLE public.newsletters RENAME TO legacy_newsletters;
    RAISE NOTICE 'archived: newsletters -> legacy_newsletters';
  ELSE
    RAISE NOTICE 'skip archive: newsletters (absent or already archived)';
  END IF;

  IF to_regclass('public.feedback') IS NOT NULL
     AND to_regclass('public.legacy_feedback') IS NULL
     AND NOT EXISTS (SELECT 1 FROM information_schema.columns
                     WHERE table_schema = 'public' AND table_name = 'feedback'
                     AND column_name = 'user_id') THEN
    ALTER TABLE public.feedback RENAME TO legacy_feedback;
    RAISE NOTICE 'archived: feedback -> legacy_feedback';
  ELSE
    RAISE NOTICE 'skip archive: feedback (absent or already archived)';
  END IF;
END
$$;

-- ----------------------------------------------------------------------------
-- 2. Create new-schema tables (exact mirror of server/src/config/supabase.ts)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS niches (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  name VARCHAR(500) NOT NULL,
  keywords TEXT[] DEFAULT '{}',
  subreddits TEXT[] DEFAULT '{}',
  blog_feeds TEXT[] DEFAULT '{}',
  include_terms TEXT[] DEFAULT '{}',
  exclude_terms TEXT[] DEFAULT '{}',
  enabled BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sources (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  platform VARCHAR(50) NOT NULL,
  status VARCHAR(50) DEFAULT 'not_configured',
  credentials JSONB DEFAULT '{}',
  last_checked TIMESTAMP,
  items_collected INTEGER DEFAULT 0,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(user_id, platform)
);

CREATE TABLE IF NOT EXISTS collected_items (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  niche_id UUID REFERENCES niches(id) ON DELETE CASCADE,
  platform VARCHAR(50) NOT NULL,
  title TEXT NOT NULL,
  url TEXT NOT NULL,
  author VARCHAR(255),
  score INTEGER DEFAULT 0,
  excerpt TEXT,
  metadata JSONB DEFAULT '{}',
  collected_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS runs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  niche_id UUID REFERENCES niches(id) ON DELETE CASCADE,
  status VARCHAR(50) DEFAULT 'pending',
  started_at TIMESTAMP DEFAULT NOW(),
  completed_at TIMESTAMP,
  stats JSONB DEFAULT '{}',
  errors TEXT[] DEFAULT '{}',
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS newsletters (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  niche_id UUID REFERENCES niches(id) ON DELETE CASCADE,
  run_id UUID REFERENCES runs(id) ON DELETE CASCADE,
  date DATE NOT NULL,
  subject TEXT NOT NULL,
  preheader TEXT,
  content JSONB NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS feedback (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  newsletter_id UUID REFERENCES newsletters(id) ON DELETE CASCADE,
  story_id VARCHAR(255) NOT NULL,
  vote VARCHAR(10) NOT NULL CHECK (vote IN ('up', 'down')),
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(user_id, newsletter_id, story_id)
);

-- ----------------------------------------------------------------------------
-- 3. Indexes (backend filters/orders on these columns)
-- ----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_niches_user_id ON niches(user_id);
CREATE INDEX IF NOT EXISTS idx_collected_items_niche_id ON collected_items(niche_id);
CREATE INDEX IF NOT EXISTS idx_collected_items_url ON collected_items(url);
CREATE INDEX IF NOT EXISTS idx_runs_user_id ON runs(user_id);
CREATE INDEX IF NOT EXISTS idx_newsletters_user_id ON newsletters(user_id);
CREATE INDEX IF NOT EXISTS idx_feedback_user_id ON feedback(user_id);

-- ----------------------------------------------------------------------------
-- 3b. Row-level security: deny-by-default on the new tables (REVIEW FIX).
--    Tables created via SQL do NOT inherit RLS; Supabase default privileges
--    would otherwise leave them readable/writable by anon/authenticated —
--    and the anon key ships inside the frontend bundle. ENABLE with zero
--    policies = default-deny for least-privilege roles. Zero functional
--    impact: the backend uses service_role (bypasses RLS) and the frontend
--    never queries tables directly (auth API only). Legacy tables are
--    deliberately left untouched (posture unchanged; see recovery plan).
--    Rerunnable: ENABLE ROW LEVEL SECURITY is idempotent.
-- ----------------------------------------------------------------------------
ALTER TABLE niches ENABLE ROW LEVEL SECURITY;
ALTER TABLE sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE collected_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE newsletters ENABLE ROW LEVEL SECURITY;
ALTER TABLE feedback ENABLE ROW LEVEL SECURITY;

-- ----------------------------------------------------------------------------
-- 4. exec_sql helper required by backend boot (server/src/config/supabase.ts).
--    Needed because the JS client has no SQL channel — DDL can only run via
--    RPC. SECURITY DEFINER (runs as owner/postgres) + executable by
--    service_role ONLY. Revoked from PUBLIC/anon/authenticated so it is
--    never reachable with the anon key. SET search_path pins unqualified
--    names to public (REVIEW FIX). CREATE OR REPLACE makes this rerunnable.
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION exec_sql(sql TEXT)
RETURNS VOID
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  EXECUTE sql;
END;
$$;

REVOKE ALL ON FUNCTION exec_sql(TEXT) FROM PUBLIC;
REVOKE ALL ON FUNCTION exec_sql(TEXT) FROM anon, authenticated;
GRANT EXECUTE ON FUNCTION exec_sql(TEXT) TO service_role;

-- ----------------------------------------------------------------------------
-- 5. Completion marker (row counts: see server/supabase-verify.sql, which
--    guards against absent tables so it works in every pre-state)
-- ----------------------------------------------------------------------------
SELECT 'migration-safe complete' AS status;
