import json
from datetime import UTC, datetime, timedelta

import httpx
from sqlalchemy import select

from app.models import Game, Match, Team
from ingestion.pandascore_client import PandaScoreClient
from ingestion.startgg import StartggClient, parse_set, sync_startgg
from ingestion.sync import refresh_rosters, refresh_stale, sync_once
from tests.sample_payloads import STARTGG_EVENT, STARTGG_SET, STARTGG_SET_TBD

NOW = datetime(2026, 11, 22, 12, 0, tzinfo=UTC)


def startgg_mock(calls: list | None = None) -> StartggClient:
    def handler(request: httpx.Request) -> httpx.Response:
        query = json.loads(request.content)["query"]
        if calls is not None:
            calls.append(query)
        if "tournaments(" in query:
            nodes = [
                {
                    "id": 1,
                    "name": "KAGARIBI #16",
                    "events": [
                        {
                            "id": 1711972,
                            "name": "Singles",
                            "numEntrants": 1536,
                            "state": "COMPLETED",
                            "videogame": {"id": 1386},
                        },
                        {
                            "id": 7,
                            "name": "Side bracket",
                            "numEntrants": 12,
                            "state": "ACTIVE",
                            "videogame": {"id": 1386},
                        },
                        {
                            "id": 8,
                            "name": "Untracked game",
                            "numEntrants": 900,
                            "state": "ACTIVE",
                            "videogame": {"id": 999},
                        },
                    ],
                }
            ]
            return httpx.Response(
                200, json={"data": {"tournaments": {"pageInfo": {"totalPages": 1}, "nodes": nodes}}}
            )
        if "phases{" in query:
            phases = [
                {"id": 2400631, "name": "TOP 1536", "numSeeds": 1536, "groupCount": 64},
                {"id": 2416736, "name": "TOP 8", "numSeeds": 8, "groupCount": 1},
            ]
            return httpx.Response(200, json={"data": {"event": {"phases": phases}}})
        sets = {"pageInfo": {"totalPages": 1}, "nodes": [STARTGG_SET, STARTGG_SET_TBD]}
        return httpx.Response(200, json={"data": {"event": {"sets": sets}}})

    return StartggClient("fake", transport=httpx.MockTransport(handler))


def fresh_cache() -> dict:
    return {"at": None, "events": [], "done": set()}


def test_parse_set_maps_players_scores_and_games():
    match, players, games = parse_set(STARTGG_SET, STARTGG_EVENT)
    assert match["id"] == -110480939 and match["source"] == "startgg"
    assert (match["status"], match["number_of_games"], match["match_type"]) == (
        "finished",
        5,
        "best_of",
    )
    assert (match["team1_score"], match["team2_score"], match["winner_id"]) == (3, 0, -24883244)
    assert (match["league_name"], match["tournament_name"]) == ("KAGARIBI #16", "TOP 8")
    assert match["stream_url"] == "https://www.twitch.tv/eastgeek"
    assert [p["name"] for p in players] == ["Hurt", "Saya"]
    assert (
        players[0]["image_url"] == "https://images.start.gg/hurt.jpg"
        and players[1]["image_url"] is None
    )
    assert [(g["position"], g["winner_id"]) for g in games] == [
        (1, -24883244),
        (2, -24883244),
        (3, -24883244),
    ]


def test_parse_set_skips_sets_without_both_entrants():
    assert parse_set(STARTGG_SET_TBD, STARTGG_EVENT) is None
    assert parse_set({**STARTGG_SET, "id": "preview_123_4"}, STARTGG_EVENT) is None


def test_sync_startgg_keeps_only_notable_final_brackets(db):
    calls = []
    cache = fresh_cache()
    assert sync_startgg(db, startgg_mock(calls), now=NOW, cache=cache) == 1
    assert [e["id"] for e in cache["events"]] == [1711972]  # small and untracked events dropped
    assert cache["events"][0]["phases"] == [2416736]  # pools are not the final bracket
    assert db.get(Match, -110480939).videogame == "ssbu"
    assert len(db.scalars(select(Game)).all()) == 3
    assert 1711972 in cache["done"]  # completed: not fetched again
    before = len(calls)
    sync_startgg(db, startgg_mock(calls), now=NOW, cache=cache)
    assert len(calls) == before


def test_pandascore_maintenance_ignores_startgg_rows(db):
    sync_startgg(db, startgg_mock(), now=NOW, cache=fresh_cache())
    match = db.get(Match, -110480939)
    match.status, match.scheduled_at = "not_started", datetime(2026, 11, 20, tzinfo=UTC)
    db.commit()
    boom = PandaScoreClient("fake", transport=httpx.MockTransport(lambda r: 1 / 0))
    assert refresh_stale(db, boom, seen=set(), now=NOW) == 0  # never asks PandaScore about it
    assert refresh_rosters(db, boom, now=NOW) == 0
    assert db.get(Team, -24883244).source == "startgg"


def test_startgg_failure_does_not_stop_pandascore(db):
    def broken(request):
        return httpx.Response(500)

    pandascore = PandaScoreClient(
        "fake", transport=httpx.MockTransport(lambda r: httpx.Response(200, json=[]))
    )
    startgg = StartggClient("fake", transport=httpx.MockTransport(broken))
    assert sync_once(db, pandascore, now=NOW, startgg=startgg) == 0  # no exception
    assert db.scalars(select(Match)).all() == []


def test_discovery_writes_staff_picks_filter_in_or_leaves_it_out(db):
    calls = []
    sync_startgg(db, startgg_mock(calls), now=NOW, cache=fresh_cache())
    tournament_queries = [q for q in calls if "tournaments(" in q]
    # start.gg treats staffPicks:null like true, so the general pass must not mention it at all
    assert ["staffPicks" in q for q in tournament_queries] == [True, False]


def test_events_far_in_the_future_are_not_polled(db):
    calls = []
    cache = {
        "at": NOW,
        "done": set(),
        "events": [
            {
                "id": 1,
                "tournament": "Later",
                "videogame": "sf6",
                "state": "CREATED",
                "start": NOW + timedelta(days=1),
                "phases": [5],
            },
        ],
    }
    assert sync_startgg(db, startgg_mock(calls), now=NOW, cache=cache) == 0
    assert calls == []
