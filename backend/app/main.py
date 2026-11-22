from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.db import Base, engine
from app.routers import health, matches

FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    # MVP: create tables on startup. Replace with Alembic migrations later.
    Base.metadata.create_all(engine)
    yield


app = FastAPI(title="Undercard", version="0.1.0", lifespan=lifespan)

# Read-only public data: any origin may GET it (needed if the front is opened from a file
# or from another local dev server).
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET"])

app.include_router(health.router)
app.include_router(matches.router)

# Serve the static front at "/" so one command runs everything locally.
# Mounted last so the API routes above take precedence.
if (FRONTEND_DIR / "index.html").exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
