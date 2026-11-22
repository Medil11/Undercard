from datetime import UTC, datetime, timedelta

import httpx
from sqlalchemy import select

from app.models import Game, Match, Player, Team
from ingestion.pandascore_client import PandaScoreClient
from ingestion.sync import (
    parse_games,
    parse_match,
    pick_stream,
    refresh_rosters,
    sync_once,
    upsert_match,
)
from tests.sample_payloads import (
    FINISHED_MATCH,
    PLAYER_MATCH,
    TEAMS_WITH_PLAYERS,
    UPCOMING_MATCH_TBD,
)


def mock_client(teams_calls: list | None = None) -> PandaScoreClient:
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path.endswith("/past"):
            return httpx.Response(200, json=[FINISHED_MATCH, PLAYER_MATCH])
        if path.endswith("/upcoming"):
            return httpx.Response(200, json=[UPCOMING_MATCH_TBD])
        if path == "/teams":
            if teams_calls is not None:
                teams_calls.append(request.url.params["filter[id]"])
            return httpx.Response(200, json=TEAMS_WITH_PLAYERS)
        return httpx.Response(200, json=[])

    return PandaScoreClient("fake", transport=httpx.MockTransport(handler))


def test_parse_match_extracts_scores_and_teams():
    match, teams = parse_match(FINISHED_MATCH)
    assert match["videogame"] == "league-of-legends"
    assert (match["number_of_games"], match["match_type"]) == (3, "best_of")
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
    client = mock_client()
    assert sync_once(db, client) == 2
    assert db.get(Match, 1001).status == "finished"
    assert db.get(Match, 1003) is None  # player vs player matches are skipped


def test_parse_games_and_stream():
    games = parse_games(FINISHED_MATCH)
    assert [(g["position"], g["winner_id"]) for g in games] == [(1, 11), (2, 12), (3, 11)]
    assert all(g["match_id"] == 1001 for g in games)
    assert pick_stream(FINISHED_MATCH["streams_list"]) == "https://example.com/main"
    assert pick_stream([]) is None


def test_upsert_stores_games_idempotently(db):
    upsert_match(db, FINISHED_MATCH)
    upsert_match(db, FINISHED_MATCH)
    db.commit()
    assert len(db.scalars(select(Game)).all()) == 3
    assert db.get(Match, 1001).stream_url == "https://example.com/main"


def test_refresh_rosters_batches_and_respects_max_age(db):
    upsert_match(db, FINISHED_MATCH)
    db.commit()
    calls: list = []
    client = mock_client(calls)
    now = datetime.now(UTC)

    assert refresh_rosters(db, client, now=now) == 2
    assert calls == ["11,12"]  # one request for every stale team
    ace = db.get(Player, 901)
    assert (ace.team_id, ace.first_name) == (11, "Jean")  # names are trimmed

    assert refresh_rosters(db, client, now=now + timedelta(hours=1)) == 0  # still fresh
    assert refresh_rosters(db, client, now=now + timedelta(days=2)) == 2
    assert len(calls) == 2


def test_refresh_rosters_detaches_players_who_left(db):
    upsert_match(db, FINISHED_MATCH)
    db.add(Player(id=999, team_id=12, name="Gone"))
    db.commit()
    refresh_rosters(db, mock_client())
    assert db.get(Player, 999).team_id is None
