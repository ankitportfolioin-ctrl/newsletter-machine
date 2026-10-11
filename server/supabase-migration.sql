-- ============================================================================
-- ⚠️ SUPERSEDED — DO NOT RUN. See server/supabase-migration-safe.sql instead.
-- This file DROPS production tables (data loss). Kept for history only.
-- ============================================================================
-- Newsletter Machine — Supabase schema migration (UNSAFE, superseded)
-- ============================================================================
-- Run this ONCE in: Supabase Dashboard → SQL Editor → New query → Run
--
-- What it does:
--   1. Drops the old single-user tables (mismatched schema, cause of 500s)
--   2. Creates the multi-user schema the backend expects (user_id columns)
--   3. Creates indexes
--   4. Creates the exec_sql helper so the backend's init is functional,
--      locked down to service_role only
--
-- WARNING: DROP TABLE deletes all rows in the old tables. Back up anything
-- you need before running.
-- ============================================================================

-- 1. Drop old / mismatched tables (dependents first, CASCADE for safety)
DROP TABLE IF EXISTS feedback CASCADE;
DROP TABLE IF EXISTS collected_items CASCADE;
DROP TABLE IF EXISTS newsletters CASCADE;
DROP TABLE IF EXISTS runs CASCADE;
DROP TABLE IF EXISTS sources CASCADE;
DROP TABLE IF EXISTS niches CASCADE;
DROP TABLE IF EXISTS item_scores CASCADE;
DROP TABLE IF EXISTS items CASCADE;
DROP TABLE IF EXISTS clusters CASCADE;
DROP TABLE IF EXISTS settings CASCADE;

-- 2. Create new-schema tables (mirrors server/src/config/supabase.ts)
CREATE TABLE niches (
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

CREATE TABLE sources (
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

CREATE TABLE collected_items (
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

CREATE TABLE runs (
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

CREATE TABLE newsletters (
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

CREATE TABLE feedback (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  newsletter_id UUID REFERENCES newsletters(id) ON DELETE CASCADE,
  story_id VARCHAR(255) NOT NULL,
  vote VARCHAR(10) NOT NULL CHECK (vote IN ('up', 'down')),
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(user_id, newsletter_id, story_id)
);

-- 3. Indexes
CREATE INDEX IF NOT EXISTS idx_niches_user_id ON niches(user_id);
CREATE INDEX IF NOT EXISTS idx_collected_items_niche_id ON collected_items(niche_id);
CREATE INDEX IF NOT EXISTS idx_collected_items_url ON collected_items(url);
CREATE INDEX IF NOT EXISTS idx_runs_user_id ON runs(user_id);
CREATE INDEX IF NOT EXISTS idx_newsletters_user_id ON newsletters(user_id);
CREATE INDEX IF NOT EXISTS idx_feedback_user_id ON feedback(user_id);

-- 4. exec_sql helper for backend init (service_role only — NOT exposed to anon)
CREATE OR REPLACE FUNCTION exec_sql(sql TEXT)
RETURNS VOID
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
  EXECUTE sql;
END;
$$;

REVOKE ALL ON FUNCTION exec_sql(TEXT) FROM PUBLIC;
REVOKE ALL ON FUNCTION exec_sql(TEXT) FROM anon, authenticated;
GRANT EXECUTE ON FUNCTION exec_sql(TEXT) TO service_role;
