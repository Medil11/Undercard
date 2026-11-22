import logging
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routers import health, internal, matches, news

# The schema is managed by Alembic: run `alembic upgrade head` before starting the app.
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
FRONTEND_DIR = Path(os.getenv("FRONTEND_DIR", Path(__file__).resolve().parents[2] / "frontend"))

app = FastAPI(title="Undercard", version="0.1.0")

# Read-only public data: any origin may GET it (needed if the front is opened from a file
# or from another local dev server).
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET"])

app.include_router(health.router)
app.include_router(matches.router)
app.include_router(news.router)
app.include_router(internal.router)

# Serve the static front at "/" so one command runs everything locally.
# Mounted last so the API routes above take precedence.
if (FRONTEND_DIR / "index.html").exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
