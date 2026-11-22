# Undercard (formerly Esport Live)

FlashScore-style live scores for esports. Personal portfolio project of a data/software engineer.
Reply to the user in French. Keep code, comments and docs in English.

## Stack

- Backend: FastAPI + SQLAlchemy 2 in `backend/app`. SQLite locally, Postgres optional (Docker Compose).
- Ingestion: `backend/ingestion`. PandaScore REST client and idempotent upserts.
- Front: one static file, `frontend/index.html` (vanilla JS). FastAPI serves it at `/`. A Next.js port is planned.
- Hosting: Supabase (Postgres + pg_cron) and one free Render web service, live at https://undercard-ong3.onrender.com. See `docs/deploy.md`.

## Commands (run from `backend/`)

```bash
pip install -e ".[dev]"
alembic upgrade head                     # create or update the schema (needed once, then after model changes)
python -m ingestion.seed_demo            # fictional demo matches, no token needed
python -m ingestion.sync                 # one sync from PandaScore (needs backend/.env)
python -m ingestion.sync --loop --interval 60
uvicorn app.main:app --reload            # front + API on http://localhost:8000
ruff check . && ruff format --check . && pytest -q
```

To reset local data: delete `backend/esport_live.db`, then `alembic upgrade head`.

## Rules

- Never commit `backend/.env`. `PANDASCORE_TOKEN` stays on the backend, never in the browser.
- Everything stays free. Accounts allowed: PandaScore, Supabase (Postgres + pg_cron) and Render (web service).
  Deployment is documented in `docs/deploy.md`; secrets live in Render's environment and Supabase Vault only.
- PandaScore conventions: Bearer auth, `page[size]` max 100, `sort=field` puts nulls first when ascending
  (use `scheduled_at`, not `begin_at`), plan limit 1,000 requests per hour. One sync cycle is at most 6 requests:
  running, upcoming (2 pages of 100), past, rosters (`/teams?filter[id]=`, 100 teams, refreshed every 24 h) and
  stale matches re-checked by id (`/matches?filter[id]=`). Matches older than 30 days are purged.
- `/health` is Render's liveness check and must always return 200. `/health/sync` reports data freshness
  (503 when the last success is over 10 minutes old) and is meant for an external uptime monitor.
- Real payload facts: `match_type` is `best_of` or `first_to` (Overwatch: `number_of_games` = wins needed).
  StarCraft 2 matches are player vs player and are skipped. Per-player stats endpoints return 403 on the free plan.
- Schema changes go through Alembic: edit `app/models.py`, then `alembic revision --autogenerate -m "..."`,
  review and commit the migration. Never `create_all` and never edit production tables by hand.
- Run lint and tests before every commit. Conventional commits, small changes.
- Do not invent API fields: check the real payload before relying on a field.

## UI direction (SofaScore-like, decided 2026-11-22)

- Product context lives in `PRODUCT.md`. `DESIGN.md` and the impeccable surface brief still describe the previous
  "Fight Night Billing" style and must be refreshed (`/impeccable document`) before relying on them.
- UI copy is in English, sentence case (no all-caps labels).
- Clean and rounded: light theme by default (#eef1f5 ground, white cards), dark theme via prefers-color-scheme.
  Cards 16px radius, logos 8px, pills and buttons fully rounded. No gradients, glows, emoji or looping animation.
- Archivo only (self-hosted in `frontend/fonts`); Anton is kept for the logo wordmark only. Yellow is in the logo only.
- Red is reserved for live status. Series state is shown as dots (one per game to win, red for the game in play).
- Match page: teams face each other around a centred score; each game is a rounded bar toward its winner,
  its length the game duration (a single dot when durations are missing).
- Team logos come from the API `image_url`; a canvas luminance check puts only very dark or very light marks on a
  contrasting tile, with an initials fallback.

## Next steps

1. Check the real data end to end (sync, then the front), fix any mismatch with the real payload.
2. Port the front to Next.js + TypeScript (`/`, `/match/[id]`, `/game/[slug]`).
3. Optional tournament tier filter (S/A/B/C), if the API payload exposes it.
