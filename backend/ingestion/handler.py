"""AWS Lambda entrypoint, triggered on a schedule by EventBridge."""

from app.config import get_settings
from app.db import SessionLocal
from ingestion.pandascore_client import PandaScoreClient
from ingestion.sync import sync_once


def lambda_handler(event: dict, context: object) -> dict:
    settings = get_settings()
    with PandaScoreClient(settings.pandascore_token, settings.pandascore_base_url) as client:
        with SessionLocal() as session:
            count = sync_once(session, client)
    return {"synced": count}
