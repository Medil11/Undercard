from datetime import UTC, datetime, timedelta

import httpx
from sqlalchemy import event, select

from app.models import Game, Match, Player, SyncStatus, Team
from ingestion.pandascore_client import PandaScoreClient
from ingestion.sync import (
    parse_games,
    parse_match,
    pick_stream,
    purge_old,
    refresh_rosters,
    refresh_stale,
    sync_once,
    upsert_match,
)
from tests.sample_payloads import (
    FINISHED_MATCH,
    PLAYER_MATCH,
    TEAMS_WITH_PLAYERS,
    UPCOMING_MATCH_TBD,
)

NOW = datetime(2026, 11, 22, 12, 0, tzinfo=UTC)  # fixed, so retention does not age the fixtures


def mock_client(teams_calls: list | None = None, by_id: list | None = None) -> PandaScoreClient:
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        first_page = request.url.params.get("page", "1") == "1"
        if path.endswith("/past"):
            return httpx.Response(200, json=[FINISHED_MATCH, PLAYER_MATCH] if first_page else [])
        if path.endswith("/upcoming"):
            return httpx.Response(200, json=[UPCOMING_MATCH_TBD] if first_page else [])
        if path == "/matches":
            return httpx.Response(200, json=by_id or [])
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
    assert sync_once(db, client, now=NOW) == 2
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


def test_sync_records_its_last_success(db):
    sync_once(db, mock_client(), now=NOW)
    status = db.get(SyncStatus, 1)
    assert status.last_count == 2 and status.last_success_at is not None


def test_refresh_stale_updates_or_removes_ghost_matches(db):
    late = {**UPCOMING_MATCH_TBD, "id": 2001, "scheduled_at": "2026-11-22T08:00:00Z"}
    gone = {**UPCOMING_MATCH_TBD, "id": 2002, "scheduled_at": "2026-11-22T09:00:00Z"}
    future = {**UPCOMING_MATCH_TBD, "id": 2003, "scheduled_at": "2026-11-23T09:00:00Z"}
    for payload in (late, gone, future):
        upsert_match(db, payload)
    db.commit()
    now_finished = {**late, "status": "finished"}
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.params["filter[id]"])
        return httpx.Response(200, json=[now_finished])

    client = PandaScoreClient("fake", transport=httpx.MockTransport(handler))
    assert refresh_stale(db, client, seen=set(), now=NOW) == 2
    assert calls == ["2001,2002"]  # one request, only late matches (not the future one)
    assert db.get(Match, 2001).status == "finished"
    assert db.get(Match, 2002) is None  # no longer known by the provider
    assert db.get(Match, 2003).status == "not_started"


def test_refresh_stale_skips_matches_seen_this_cycle(db):
    upsert_match(db, {**UPCOMING_MATCH_TBD, "id": 2001, "scheduled_at": "2026-11-22T08:00:00Z"})
    db.commit()
    client = PandaScoreClient("fake", transport=httpx.MockTransport(lambda r: 1 / 0))
    assert refresh_stale(db, client, seen={2001}, now=NOW) == 0


def test_purge_old_removes_matches_and_games(db):
    upsert_match(db, FINISHED_MATCH)  # 2026-11-20, with 3 games
    db.commit()
    assert purge_old(db, NOW + timedelta(days=27)) == 0  # 2026-11-20 is still within 30 days
    assert purge_old(db, NOW + timedelta(days=31)) == 1
    assert db.get(Match, 1001) is None
    assert db.scalars(select(Game)).all() == []


def test_parse_player_reads_the_birthday():
    from datetime import date

    from ingestion.sync import parse_player

    assert parse_player({"id": 1, "name": "A", "birthday": "1995-04-20"}, 11)["birthday"] == date(
        1995, 4, 20
    )
    assert parse_player({"id": 1, "name": "A", "birthday": None}, 11)["birthday"] is None


def test_unchanged_match_is_not_read_again(db):
    upsert_match(db, FINISHED_MATCH)
    db.commit()
    statements = []
    event.listen(db.get_bind(), "before_cursor_execute", lambda *a: statements.append(a[2]))
    upsert_match(db, FINISHED_MATCH)
    assert statements == []
    upsert_match(db, {**FINISHED_MATCH, "name": "renamed"})
    db.commit()
    assert statements
