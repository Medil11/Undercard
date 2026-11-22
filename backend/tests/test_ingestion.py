import httpx
from sqlalchemy import select

from app.models import Match, Team
from ingestion.pandascore_client import PandaScoreClient
from ingestion.sync import parse_match, sync_once, upsert_match
from tests.sample_payloads import FINISHED_MATCH, UPCOMING_MATCH_TBD


def test_parse_match_extracts_scores_and_teams():
    match, teams = parse_match(FINISHED_MATCH)
    assert match["videogame"] == "league-of-legends"
    assert (match["team1_score"], match["team2_score"]) == (2, 1)
    assert match["winner_id"] == 11
    assert [t["id"] for t in teams] == [11, 12]


def test_parse_match_handles_tbd_opponents():
    match, teams = parse_match(UPCOMING_MATCH_TBD)
    assert match["team1_id"] is None and match["team2_id"] is None
    assert teams == []


def test_upsert_is_idempotent(db):
    upsert_match(db, FINISHED_MATCH)
    upsert_match(db, FINISHED_MATCH)
    db.commit()
    assert len(db.scalars(select(Match)).all()) == 1
    assert len(db.scalars(select(Team)).all()) == 2


def test_sync_once_with_mocked_api(db):
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/past"):
            return httpx.Response(200, json=[FINISHED_MATCH])
        if request.url.path.endswith("/upcoming"):
            return httpx.Response(200, json=[UPCOMING_MATCH_TBD])
        return httpx.Response(200, json=[])

    client = PandaScoreClient("fake", transport=httpx.MockTransport(handler))
    assert sync_once(db, client) == 2
    assert db.get(Match, 1001).status == "finished"
