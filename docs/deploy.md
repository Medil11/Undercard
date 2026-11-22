# Deploy: Supabase + Render (free)

```
Supabase pg_cron (every minute) --POST /internal/sync--> Render: FastAPI + front + ingestion --> PandaScore
                                                                  |
Browser -----------------------------------------------------------+--> Supabase Postgres
```

- **Supabase** hosts PostgreSQL (free: 500 MB) and runs the scheduler (`pg_cron` + `pg_net`).
- **Render** runs one free web service: the API, the static front, and the sync triggered by the scheduler.
  The call every minute also keeps the instance awake. One always-on service uses about 744 of the
  750 free hours a month, so keep it the only free service in the Render workspace.
- The PandaScore token only lives in Render's environment. One cycle is at most 6 requests (live, 2 pages
  of upcoming, past, 1 batch of rosters, 1 batch of stale matches re-checked by id), so at most 360 per hour
  out of the 1,000 allowed.
- Matches older than 30 days are deleted at the end of each cycle, so the database stays small.

## 1. Supabase project

1. Create a project (region close to Render's, e.g. Frankfurt). Save the database password.
2. **Connect** > **Session pooler**: copy the URI. It looks like
   `postgresql://postgres.<ref>:<password>@aws-0-eu-central-1.pooler.supabase.com:5432/postgres`.
   Use the session pooler: Render has no IPv6, and the direct connection needs it.
3. Replace `[YOUR-PASSWORD]` and add `?sslmode=require` at the end. This is `DATABASE_URL`.

## 2. Render service

1. **New** > **Blueprint**, connect the GitHub repository. Render reads `render.yaml`.
2. Fill `DATABASE_URL` (step 1) and `PANDASCORE_TOKEN`. `SYNC_SECRET` is generated for you.
3. Deploy. The start command runs `alembic upgrade head` first, so the tables are created on Supabase.
4. Check `https://<service>.onrender.com/health` returns `{"status":"ok"}`.
5. Open the service's **Environment** tab and copy the generated `SYNC_SECRET` value.

## 3. Scheduler

1. Open `docs/deploy/supabase_cron.sql`, replace the service URL and the `SYNC_SECRET` placeholders.
2. Paste it into the Supabase **SQL editor** and run it.
3. Within two minutes, Render's logs show `synced N matches` every minute, and the site has data.
   The checks at the bottom of the SQL file show the job runs and the HTTP responses (expect 202).

## 4. Monitoring (recommended)

`GET /health/sync` returns `200` while the last successful sync is under 10 minutes old, and `503` otherwise,
with the last error in the body. Point a free uptime monitor at it to get an email when ingestion stops
(expired token, PandaScore quota, Render hours used up):

1. Create a free account on an uptime service such as UptimeRobot.
2. Add an HTTP(s) monitor on `https://<service>.onrender.com/health/sync`, every 5 minutes.
3. Set the alert contact to your email. A `503` or a timeout raises an alert.

Keep `/health` (always `200`) as Render's health check: Render restarts services whose health check fails,
and a stale sync is not a reason to restart the web service.

## Updating

- Code: push to `main`; Render redeploys and runs pending migrations on start.
- Schema: change `app/models.py`, then `cd backend && alembic revision --autogenerate -m "..."`,
  review the file, commit it. Never edit the Supabase tables by hand.

## Troubleshooting

- `403` in `net._http_response`: the secret in Vault differs from Render's `SYNC_SECRET`.
- `404`: `SYNC_SECRET` is empty on Render.
- Timeouts right after a deploy: the instance is starting; the next minute succeeds.
- No data: check `PANDASCORE_TOKEN` and Render's logs for `scheduled sync failed`.
