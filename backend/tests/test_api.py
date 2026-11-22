from datetime import UTC, datetime, timedelta

from app.models import Player
from ingestion.sync import record_sync, upsert_match
from tests.sample_payloads import FINISHED_MATCH, UPCOMING_MATCH_TBD


def seed(db):
    upsert_match(db, FINISHED_MATCH)
    upsert_match(db, UPCOMING_MATCH_TBD)
    db.commit()


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_list_and_filter_matches(client, db):
    seed(db)
    assert len(client.get("/matches").json()) == 2
    finished = client.get("/matches", params={"status": "finished"}).json()
    assert [m["id"] for m in finished] == [1001]
    assert finished[0]["team1"]["name"] == "Alpha"
    cs = client.get("/matches", params={"videogame": "cs-go"}).json()
    assert [m["id"] for m in cs] == [1002]


def test_get_match_and_404(client, db):
    seed(db)
    assert client.get("/matches/1001").json()["team1_score"] == 2
    assert client.get("/matches/999").status_code == 404


def test_match_detail_has_games_players_and_stream(client, db):
    seed(db)
    db.add(Player(id=901, team_id=11, name="Ace", nationality="FR"))
    db.commit()
    detail = client.get("/matches/1001").json()
    assert [g["winner_id"] for g in detail["games"]] == [11, 12, 11]
    assert [p["name"] for p in detail["team1"]["players"]] == ["Ace"]
    assert detail["team2"]["players"] == []
    assert detail["stream_url"] == "https://example.com/main"
    # The list stays light: no rosters or games.
    listed = client.get("/matches").json()[0]
    assert "games" not in listed and "players" not in (listed["team1"] or {})


def test_videogames(client, db):
    seed(db)
    slugs = {v["slug"]: v["matches"] for v in client.get("/videogames").json()}
    assert slugs == {"cs-go": 1, "league-of-legends": 1}


def test_list_matches_by_date_window(client, db):
    seed(db)  # finished on 2026-11-20, upcoming on 2026-11-25
    day = client.get(
        "/matches", params={"since": "2026-11-20T00:00:00Z", "until": "2026-11-21T00:00:00Z"}
    )
    assert [m["id"] for m in day.json()] == [1001]
    later = client.get("/matches", params={"since": "2026-11-21T00:00:00Z"})
    assert [m["id"] for m in later.json()] == [1002]


def test_health_sync_reports_freshness(client, db):
    assert client.get("/health/sync").status_code == 503  # never synced
    record_sync(db, datetime.now(UTC), count=7)
    body = client.get("/health/sync").json()
    assert (body["status"], body["last_count"]) == ("ok", 7)
    record_sync(db, datetime.now(UTC) - timedelta(minutes=30), count=7)
    stale = client.get("/health/sync")
    assert (stale.status_code, stale.json()["status"]) == (503, "stale")


def test_times_are_returned_with_a_timezone(client, db):
    seed(db)
    assert client.get("/matches/1001").json()["scheduled_at"].endswith(("Z", "+00:00"))


def test_team_filter_matches_the_name_in_any_game(client, db):
    seed(db)  # FINISHED_MATCH is Alpha vs Beta
    upsert_match(db, {**FINISHED_MATCH, "id": 1004, "videogame": {"slug": "valorant"}})
    db.commit()
    ids = [m["id"] for m in client.get("/matches", params={"team": "alpha"}).json()]
    assert sorted(ids) == [1001, 1004]
    assert client.get("/matches", params={"team": "Nobody"}).json() == []


def test_search_teams(client, db):
    seed(db)
    assert client.get("/teams", params={"q": "alp"}).json() == [
        {"name": "Alpha", "image_url": None}
    ]
    assert client.get("/teams", params={"q": "a"}).status_code == 422  # two characters minimum


def test_match_has_league_tournament_and_serie_details(client, db):
    seed(db)
    m = client.get("/matches/1001").json()
    assert m["league_image_url"] == "https://example.com/league.png"
    assert (m["prizepool"], m["region"], m["country"]) == (
        "50000 United States Dollar",
        "WEU",
        "FR",
    )
    assert (m["serie_name"], m["season"], m["year"]) == ("Spring 2026", "Spring", 2026)


def test_standings_are_fetched_once_then_cached(client, db, monkeypatch):
    from app.routers import matches

    seed(db)
    calls = []
    row = {
        "rank": 1,
        "team": {"id": 11, "name": "Alpha"},
        "last_match": {"id": 1001, "name": "Final", "status": "finished", "winner_id": 11},
    }

    def fake(self, tournament_id):
        calls.append(tournament_id)
        return [row]

    monkeypatch.setattr(matches.PandaScoreClient, "standings", fake)
    monkeypatch.setattr(matches, "_standings", {})
    first = client.get("/matches/1001/standings").json()
    assert first[0]["rank"] == 1 and first[0]["team"]["name"] == "Alpha"
    client.get("/matches/1001/standings")
    assert calls == [77]  # second call served from the cache
    assert client.get("/matches/1002/standings").json() == []  # no tournament id
    assert client.get("/matches/999/standings").status_code == 404


def test_leagues_of_a_game_and_league_filter(client, db):
    seed(db)
    assert client.get("/leagues", params={"videogame": "league-of-legends"}).json() == [
        {"name": "Demo League", "image_url": "https://example.com/league.png", "matches": 1}
    ]
    assert client.get("/leagues", params={"videogame": "dota-2"}).json() == []
    by_league = client.get("/matches", params={"league": "Demo League"}).json()
    assert sorted(m["id"] for m in by_league) == [1001, 1002]
    assert client.get("/matches", params={"league": "Other"}).json() == []


def test_team_and_player_pages(client, db):
    from datetime import date

    seed(db)
    db.add(Player(id=901, team_id=11, name="Ace", nationality="FR", birthday=date(2001, 5, 4)))
    db.commit()
    team = client.get("/teams/11").json()
    assert team["name"] == "Alpha" and [p["name"] for p in team["players"]] == ["Ace"]
    player = client.get("/players/901").json()
    assert player["team"]["name"] == "Alpha" and player["birthday"] == "2001-05-04"
    assert client.get("/teams/999").status_code == 404
    assert client.get("/players/999").status_code == 404
    assert [m["id"] for m in client.get("/matches", params={"team_id": 12}).json()] == [1001]
    assert client.get("/matches/1001").json()["tier"] == "a"
