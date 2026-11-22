FINISHED_MATCH = {
    "id": 1001,
    "name": "Final: Alpha vs Beta",
    "status": "finished",
    "scheduled_at": "2026-11-20T18:00:00Z",
    "begin_at": "2026-11-20T18:05:00Z",
    "end_at": "2026-11-20T19:40:00Z",
    "number_of_games": 3,
    "match_type": "best_of",
    "winner_id": 11,
    "videogame": {"slug": "league-of-legends"},
    "league": {"name": "Demo League"},
    "tournament": {"name": "Playoffs"},
    "opponents": [
        {"opponent": {"id": 11, "name": "Alpha", "acronym": "ALP", "image_url": None}},
        {"opponent": {"id": 12, "name": "Beta", "acronym": "BET", "image_url": None}},
    ],
    "results": [{"team_id": 11, "score": 2}, {"team_id": 12, "score": 1}],
    "games": [
        {"id": 5001, "position": 1, "status": "finished", "length": 1900, "winner": {"id": 11}},
        {"id": 5002, "position": 2, "status": "finished", "length": 2100, "winner": {"id": 12}},
        {"id": 5003, "position": 3, "status": "finished", "length": 1700, "winner": {"id": 11}},
    ],
    "streams_list": [
        {"main": False, "official": True, "raw_url": "https://example.com/official"},
        {"main": True, "official": True, "raw_url": "https://example.com/main"},
    ],
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

PLAYER_MATCH = {
    **FINISHED_MATCH,
    "id": 1003,
    "videogame": {"slug": "starcraft-2"},
    "opponents": [
        {"type": "Player", "opponent": {"id": 43042, "name": "P1", "image_url": None}},
        {"type": "Player", "opponent": {"id": 43506, "name": "P2", "image_url": None}},
    ],
    "results": [{"player_id": 43042, "score": 0}, {"player_id": 43506, "score": 0}],
}

# Shape of GET /teams?filter[id]=11,12 (players trimmed to the fields we store).
TEAMS_WITH_PLAYERS = [
    {
        "id": 11,
        "players": [
            {
                "id": 901,
                "name": "Ace",
                "first_name": "Jean ",
                "last_name": "Dupont",
                "role": None,
                "nationality": "FR",
                "image_url": None,
            },
            {
                "id": 902,
                "name": "Bolt",
                "first_name": None,
                "last_name": None,
                "role": "awper",
                "nationality": "DE",
                "image_url": None,
            },
        ],
    },
    {"id": 12, "players": []},
]
