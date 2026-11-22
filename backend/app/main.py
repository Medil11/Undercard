from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db import Base, engine
from app.routers import health, matches


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    # MVP: create tables on startup. Replace with Alembic migrations later.
    Base.metadata.create_all(engine)
    yield


app = FastAPI(title="Esport Live", version="0.1.0", lifespan=lifespan)
app.include_router(health.router)
app.include_router(matches.router)
