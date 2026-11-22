# Esport Live

FlashScore-style live scores for esports. Personal portfolio project of a data/software engineer.
Reply to the user in French. Keep code, comments and docs in English.

## Stack

- Backend: FastAPI + SQLAlchemy 2 in `backend/app`. SQLite locally, Postgres optional (Docker Compose).
- Ingestion: `backend/ingestion`. PandaScore REST client and idempotent upserts.
- Front: one static file, `frontend/index.html` (vanilla JS). FastAPI serves it at `/`. A Next.js port is planned.
- Infra: `infra/terraform` is a skeleton (Lambda + EventBridge), not applied.

## Commands (run from `backend/`)

```bash
pip install -e ".[dev]"
python -m ingestion.seed_demo            # fictional demo matches, no token needed
python -m ingestion.sync                 # one sync from PandaScore (needs backend/.env)
python -m ingestion.sync --loop --interval 60
uvicorn app.main:app --reload            # front + API on http://localhost:8000
ruff check . && ruff format --check . && pytest -q
```

Delete `backend/esport_live.db` to reset the local data.

## Rules

- Never commit `backend/.env`. `PANDASCORE_TOKEN` stays on the backend, never in the browser.
- Everything stays free and local for now. No paid service, no account other than the PandaScore token.
- PandaScore conventions: Bearer auth, `page[size]` max 100, `sort=field` puts nulls first when ascending
  (use `scheduled_at`, not `begin_at`), plan limit 1,000 requests per hour, one sync cycle = 3 requests
  plus at most 1 for rosters (`/teams?filter[id]=`, 100 teams per call, refreshed every 24 h).
- Real payload facts: `match_type` is `best_of` or `first_to` (Overwatch: `number_of_games` = wins needed).
  StarCraft 2 matches are player vs player and are skipped. Per-player stats endpoints return 403 on the free plan.
- Schema changes have no migrations yet: delete `backend/esport_live.db` after changing `app/models.py`.
- Run lint and tests before every commit. Conventional commits, small changes.
- Do not invent API fields: check the real payload before relying on a field.

## UI direction (already decided, keep it)

- Neutral graphite surfaces, red used only for live status. 4px spacing grid, weights 400 to 600.
- No gradients, glows, emoji or looping animation. One easing, small transitions.
- Signature detail: series pips (one square per map to win in a BO3 or BO5), only on live and finished rows.
- Team logos come from the API `image_url`, with a neutral initials fallback.
- Reference for density and structure: Liquipedia (Upcoming / Completed tabs, explicit BO format).

## Next steps

1. Check the real data end to end (sync, then the front), fix any mismatch with the real payload.
2. Port the front to Next.js + TypeScript (`/`, `/match/[id]`, `/game/[slug]`).
3. Optional tournament tier filter (S/A/B/C), if the API payload exposes it.
