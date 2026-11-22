from ingestion.seed_demo import DEMO, seed


def test_seed_populates_the_api(client, db):
    assert seed(db) == len(DEMO)
    matches = client.get("/matches").json()
    assert len(matches) == len(DEMO)
    assert {m["status"] for m in matches} == {"running", "not_started", "finished"}
    games = {v["slug"] for v in client.get("/videogames").json()}
    assert "league-of-legends" in games and "cs-go" in games
