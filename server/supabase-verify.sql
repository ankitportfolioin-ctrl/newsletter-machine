-- ============================================================================
-- Newsletter Machine — post-migration verification (READ-ONLY, safe anytime)
-- ============================================================================
-- Run in: Supabase Dashboard → SQL Editor → New query → paste → Run
-- Every query is a SELECT: nothing is created, altered, or deleted.
-- Run BEFORE the migration to record the baseline, and AFTER to verify.
-- ============================================================================

-- 1. Which app tables exist? (expected after migration: the 6 new tables;
--    legacy_* tables present only if archiving ran)
SELECT tablename AS new_tables_present
FROM pg_tables
WHERE schemaname = 'public'
  AND tablename IN ('niches','sources','collected_items','runs',
                    'newsletters','feedback')
ORDER BY 1;

SELECT tablename AS legacy_tables_present
FROM pg_tables
WHERE schemaname = 'public'
  AND tablename IN ('legacy_niches','legacy_sources','legacy_runs',
                    'legacy_newsletters','legacy_feedback',
                    'items','clusters','settings','item_scores')
ORDER BY 1;

-- 2. Presence probe, guarded so missing tables report instead of erroring
--    (exact counts: see query 3; run only its lines for present tables)
DO $$
DECLARE
  t TEXT;
BEGIN
  FOREACH t IN ARRAY ARRAY[
    'niches','sources','collected_items','runs','newsletters','feedback',
    'legacy_niches','legacy_sources','legacy_runs',
    'legacy_newsletters','legacy_feedback',
    'items','clusters','settings','item_scores'
  ] LOOP
    IF to_regclass('public.' || t) IS NOT NULL THEN
      RAISE NOTICE '%: present', t;
    ELSE
      RAISE NOTICE '%: ABSENT', t;
    END IF;
  END LOOP;
END
$$;

-- 3. Exact row counts, guarded so absent tables report instead of aborting
--    the script (safe to run pre-migration, when most tables don't exist)
DO $$
DECLARE
  t TEXT;
  c BIGINT;
BEGIN
  FOREACH t IN ARRAY ARRAY[
    'niches','sources','collected_items','runs','newsletters','feedback',
    'legacy_niches','legacy_sources','legacy_runs',
    'legacy_newsletters','legacy_feedback',
    'items','clusters','settings','item_scores'
  ] LOOP
    IF to_regclass('public.' || t) IS NOT NULL THEN
      EXECUTE format('SELECT COUNT(*) FROM public.%I', t) INTO c;
      RAISE NOTICE '%: % rows', t, c;
    ELSE
      RAISE NOTICE '%: ABSENT (no count)', t;
    END IF;
  END LOOP;
END
$$;

-- 4. Column inventory of the new tables (must include user_id UUID, and
--    collected_items must include niche_id/url/title)
SELECT table_name, column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name IN ('niches','sources','collected_items','runs',
                     'newsletters','feedback')
ORDER BY table_name, ordinal_position;

-- 5. Required indexes present?
SELECT indexname, tablename
FROM pg_indexes
WHERE schemaname = 'public'
  AND indexname IN ('idx_niches_user_id','idx_collected_items_niche_id',
                    'idx_collected_items_url','idx_runs_user_id',
                    'idx_newsletters_user_id','idx_feedback_user_id')
ORDER BY 1;

-- 6. Required UNIQUE constraints for upserts
--    (feedback: user_id+newsletter_id+story_id; sources: user_id+platform)
SELECT conrelid::regclass AS table_name, conname AS constraint_name,
       pg_get_constraintdef(oid) AS definition
FROM pg_constraint
WHERE connamespace = 'public'::regnamespace
  AND contype = 'u'
  AND conrelid::regclass::text IN ('sources','feedback');

-- 7. Required foreign keys (user_id → auth.users; niche_id/run_id/newsletter_id
--    chains; these power the PostgREST embedded joins `niches(name)`)
SELECT conrelid::regclass AS from_table, conname AS fk_name,
       pg_get_constraintdef(oid) AS definition
FROM pg_constraint
WHERE connamespace = 'public'::regnamespace
  AND contype = 'f'
  AND conrelid::regclass::text
      IN ('niches','sources','collected_items','runs','newsletters','feedback')
ORDER BY 1;

-- 8. RLS posture (expected after safe migration: rls_enabled = true on all
--    six new tables, zero policies = default-deny for anon/authenticated.
--    Backend uses service_role, which bypasses RLS. Do NOT add permissive
--    policies or disable RLS to fix app errors — app errors are never RLS
--    errors while service_role is used.)
SELECT tablename, rowsecurity AS rls_enabled
FROM pg_tables
WHERE schemaname = 'public'
  AND tablename IN ('niches','sources','collected_items','runs',
                    'newsletters','feedback')
ORDER BY 1;

SELECT schemaname, tablename, policyname, roles, cmd, qual, with_check
FROM pg_policies
WHERE schemaname = 'public'
  AND tablename IN ('niches','sources','collected_items','runs',
                    'newsletters','feedback');

-- 9. exec_sql helper present and locked to service_role?
SELECT p.proname,
       has_function_privilege('anon', p.oid, 'EXECUTE') AS anon_can_exec,
       has_function_privilege('authenticated', p.oid, 'EXECUTE') AS auth_can_exec,
       has_function_privilege('service_role', p.oid, 'EXECUTE') AS service_can_exec
FROM pg_proc p
JOIN pg_namespace n ON n.oid = p.pronamespace
WHERE n.nspname = 'public' AND p.proname = 'exec_sql';

-- 10. pgcrypto available (gen_random_uuid dependency)?
SELECT * FROM pg_extension WHERE extname = 'pgcrypto';

-- 11. auth.users sanity (count only — never dump user rows)
SELECT COUNT(*) AS auth_user_count FROM auth.users;
