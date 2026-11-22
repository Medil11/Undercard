-- Undercard: run one ingestion cycle every minute from Supabase.
-- Paste into the Supabase SQL editor AFTER the Render service is live.
-- Replace the two placeholders first. Safe to re-run: it updates the job in place.

-- 1. Extensions (also listed under Database > Extensions in the dashboard).
create extension if not exists pg_cron;
create extension if not exists pg_net;

-- 2. Keep the URL and the shared secret in Vault, not in the job text.
--    The secret is the SYNC_SECRET value from the Render service's Environment tab.
select vault.create_secret('https://REPLACE-WITH-YOUR-SERVICE.onrender.com', 'undercard_url')
where not exists (select 1 from vault.secrets where name = 'undercard_url');
select vault.create_secret('REPLACE-WITH-SYNC_SECRET-FROM-RENDER', 'undercard_sync_secret')
where not exists (select 1 from vault.secrets where name = 'undercard_sync_secret');

-- 3. Every minute: POST /internal/sync. The app answers 202 at once and syncs in the background.
select cron.schedule(
  'undercard-sync',
  '* * * * *',
  $$
  select net.http_post(
    url := (select decrypted_secret from vault.decrypted_secrets where name = 'undercard_url')
           || '/internal/sync',
    headers := jsonb_build_object(
      'Content-Type', 'application/json',
      'X-Sync-Secret', (select decrypted_secret from vault.decrypted_secrets where name = 'undercard_sync_secret')
    ),
    body := '{}'::jsonb,
    timeout_milliseconds := 10000
  );
  $$
);

-- 4. Keep the free 500 MB database small: drop cron run history older than a day.
select cron.schedule(
  'undercard-cron-cleanup',
  '17 3 * * *',
  $$ delete from cron.job_run_details where end_time < now() - interval '1 day' $$
);

-- Checks:
--   select jobname, schedule, active from cron.job;
--   select status, return_message, start_time from cron.job_run_details order by start_time desc limit 5;
--   select status_code, content, created from net._http_response order by created desc limit 5;
-- Fix a placeholder later:
--   select vault.update_secret((select id from vault.secrets where name = 'undercard_url'), 'https://...');
-- Stop everything:
--   select cron.unschedule('undercard-sync'); select cron.unschedule('undercard-cron-cleanup');
