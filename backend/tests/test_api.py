from ingestion.sync import upsert_match
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


def test_videogames(client, db):
    seed(db)
    slugs = {v["slug"]: v["matches"] for v in client.get("/videogames").json()}
    assert slugs == {"cs-go": 1, "league-of-legends": 1}
