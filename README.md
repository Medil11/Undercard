# Esport Live

FlashScore-style live scores for esports: matches in progress, upcoming fixtures and results across the major games (League of Legends, CS2, Dota 2, Valorant, ...).

Personal project built to practice an end-to-end data product: ingestion, storage, API, infrastructure as code and CI.

## Features

- Ingestion from the [PandaScore](https://developers.pandascore.co) API (running, upcoming and past matches), idempotent upserts
- REST API: filter by status and game, match details
- Multi-game data model
- Tests (API and ingestion with a mocked provider), lint, GitHub Actions CI
- Docker Compose for local development, Terraform skeleton for AWS (Lambda + EventBridge)

## Architecture

See [docs/architecture.md](docs/architecture.md).

```
PandaScore -> Ingestion (Lambda/worker) -> PostgreSQL -> FastAPI -> Frontend
```

## Quick start

```bash
cp .env.example .env        # add your PandaScore token
docker compose up --build   # db + api + ingestion worker
```

API docs: http://localhost:8000/docs

Without Docker:

```bash
make install
make test
PANDASCORE_TOKEN=... make sync   # one-off sync into a local SQLite file
make dev                         # API on :8000
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
