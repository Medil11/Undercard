from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import SyncStatus

router = APIRouter(tags=["health"])

STALE_SECONDS = 10 * 60  # the sync runs every minute in production


@router.get("/health")
def health() -> dict[str, str]:
    """Liveness for the host. Always 200 while the process runs (Render uses it on deploy)."""
    return {"status": "ok"}


@router.get("/health/sync")
def health_sync(response: Response, db: Session = Depends(get_db)) -> dict:
    """Freshness of the data, for an uptime monitor: 503 when no sync succeeded recently."""
    row = db.get(SyncStatus, 1)
    last = row.last_success_at if row else None
    if last is not None and last.tzinfo is None:  # SQLite drops the timezone
        last = last.replace(tzinfo=UTC)
    age = int((datetime.now(UTC) - last).total_seconds()) if last else None
    ok = age is not None and age <= STALE_SECONDS
    if not ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {
        "status": "ok" if ok else "stale",
        "last_success_at": last.isoformat() if last else None,
        "age_seconds": age,
        "last_count": row.last_count if row else None,
        "last_error_at": row.last_error_at.isoformat() if row and row.last_error_at else None,
        "last_error": row.last_error if row else None,
    }
