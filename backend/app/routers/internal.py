"""Trigger one ingestion cycle over HTTP.

In production a Supabase pg_cron job calls this route every minute (see docs/deploy.md).
The call also keeps the free Render instance awake.
"""

import hmac
import logging
import threading
from datetime import UTC, datetime

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, status

from app.config import get_settings
from app.db import SessionLocal
from ingestion.pandascore_client import PandaScoreClient
from ingestion.sync import record_sync, sync_once

router = APIRouter(tags=["internal"], include_in_schema=False)
log = logging.getLogger("ingestion")
_running = threading.Lock()  # one cycle at a time, even if calls pile up


def run_sync() -> None:
    try:
        settings = get_settings()
        with PandaScoreClient(settings.pandascore_token, settings.pandascore_base_url) as client:
            with SessionLocal() as session:
                sync_once(session, client)
    except Exception as exc:
        log.exception("scheduled sync failed")
        try:
            with SessionLocal() as session:
                record_sync(session, datetime.now(UTC), error=repr(exc))
        except Exception:
            log.exception("could not record the sync failure")
    finally:
        _running.release()


@router.post("/internal/sync", status_code=status.HTTP_202_ACCEPTED)
def trigger_sync(
    background: BackgroundTasks, x_sync_secret: str = Header(default="")
) -> dict[str, str]:
    secret = get_settings().sync_secret
    if not secret:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    if not hmac.compare_digest(x_sync_secret.encode(), secret.encode()):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Invalid sync secret")
    if not _running.acquire(blocking=False):
        return {"status": "already running"}
    background.add_task(run_sync)  # runs after the response, so the caller never waits
    return {"status": "started"}
