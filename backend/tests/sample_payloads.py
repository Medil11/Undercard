FINISHED_MATCH = {
    "id": 1001,
    "name": "Final: Alpha vs Beta",
    "status": "finished",
    "scheduled_at": "2026-11-20T18:00:00Z",
    "begin_at": "2026-11-20T18:05:00Z",
    "end_at": "2026-11-20T19:40:00Z",
    "number_of_games": 3,
    "winner_id": 11,
    "videogame": {"slug": "league-of-legends"},
    "league": {"name": "Demo League"},
    "tournament": {"name": "Playoffs"},
    "opponents": [
        {"opponent": {"id": 11, "name": "Alpha", "acronym": "ALP", "image_url": None}},
        {"opponent": {"id": 12, "name": "Beta", "acronym": "BET", "image_url": None}},
    ],
    "results": [{"team_id": 11, "score": 2}, {"team_id": 12, "score": 1}],
}

UPCOMING_MATCH_TBD = {
    "id": 1002,
    "name": "Semi-final: TBD vs TBD",
    "status": "not_started",
    "scheduled_at": "2026-11-25T18:00:00Z",
    "begin_at": None,
    "end_at": None,
    "number_of_games": 3,
    "winner_id": None,
    "videogame": {"slug": "cs-go"},
    "league": {"name": "Demo League"},
    "tournament": {"name": "Playoffs"},
    "opponents": [],
    "results": [],
}
