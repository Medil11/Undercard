# Undercard

![Undercard](frontend/logo.svg)

FlashScore-style live scores for esports: matches in progress, upcoming fixtures and results across the major games (League of Legends, CS2, Dota 2, Valorant, ...).

Personal project built to practice an end-to-end data product: ingestion, storage, API, infrastructure as code and CI.

## Features

- Ingestion from the [PandaScore](https://developers.pandascore.co) API (running, upcoming and past matches), idempotent upserts
- REST API: filter by status and game, match details
- Multi-game data model
- Tests (API and ingestion with a mocked provider), lint, GitHub Actions CI
- Runs locally with a demo seed, Docker Compose available, Terraform skeleton for AWS (Lambda + EventBridge)

## Architecture

See [docs/architecture.md](docs/architecture.md).

```
PandaScore -> Ingestion (Lambda/worker) -> PostgreSQL -> FastAPI -> Frontend
```

## Run locally (no external service)

You only need Python 3.11+. No account, no token, no Docker.

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows PowerShell: .\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
python -m ingestion.seed_demo    # fills a local SQLite file with fictional matches
uvicorn app.main:app --reload
```

Open http://localhost:8000: FastAPI serves the front (`frontend/index.html`) and the API.
Interactive API docs: http://localhost:8000/docs.

To reset the demo data, delete `backend/esport_live.db` and run the seed again.

### Real data (optional)

Create `backend/.env` with a free [PandaScore](https://developers.pandascore.co) token:

```
PANDASCORE_TOKEN=your_token_here
```

Then run `python -m ingestion.sync` (once) or `python -m ingestion.sync --loop --interval 60`.
This is the only call to an external service, and it is optional.

### Docker Compose (optional)

```bash
cp .env.example .env
docker compose up --build   # Postgres + API + ingestion worker
```

## API

| Endpoint | Description |
|---|---|
| `GET /health` | Health check |
| `GET /matches?status=running&videogame=cs-go&limit=50` | List matches |
| `GET /matches/{id}` | Match detail |
| `GET /videogames` | Games present in the database, with match counts |

## Project layout

```
backend/    FastAPI app, ingestion, tests
frontend/   Next.js app (planned)
infra/      Terraform/OpenTofu
docs/       Architecture, data model, roadmap
scripts/    Lambda packaging
```

## Roadmap

See [docs/roadmap.md](docs/roadmap.md).

## Data and licence

Match data belongs to PandaScore and is subject to their terms. This project is for learning purposes. Code under the MIT licence.
