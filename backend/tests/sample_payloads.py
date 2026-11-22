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
    "league": {"name": "Demo League", "image_url": "https://example.com/league.png"},
    "tournament": {
        "id": 77,
        "tier": "a",
        "name": "Playoffs",
        "prizepool": "50000 United States Dollar",
        "region": "WEU",
        "country": "FR",
    },
    "serie": {"full_name": "Spring 2026", "season": "Spring", "year": 2026},
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

# Shapes copied from real start.gg responses (KAGARIBI #16 Top 8), trimmed.
STARTGG_EVENT = {
    "id": 1711972,
    "tournament": "KAGARIBI #16",
    "videogame": "ssbu",
    "state": "COMPLETED",
    "phases": [2416736],
}
STARTGG_SET = {
    "id": 110480939,
    "bestOf": 3,
    "totalGames": 5,
    "fullRoundText": "Grand Final",
    "startAt": None,
    "startedAt": 1795347416,
    "completedAt": 1795347416,
    "winnerId": 24883244,
    "phaseGroup": {"phase": {"name": "TOP 8"}},
    "stream": {"streamName": "eastgeek", "streamSource": "TWITCH"},
    "games": [
        {"id": 901, "orderNum": 1, "winnerId": 24883244},
        {"id": 902, "orderNum": 2, "winnerId": 24883244},
        {"id": 903, "orderNum": 3, "winnerId": 24883244},
    ],
    "slots": [
        {
            "entrant": {
                "id": 24883244,
                "name": "E36 | Hurt",
                "participants": [
                    {
                        "gamerTag": "Hurt",
                        "prefix": "E36",
                        "user": {"images": [{"url": "https://images.start.gg/hurt.jpg"}]},
                    }
                ],
            },
            "standing": {"stats": {"score": {"value": 3}}},
        },
        {
            "entrant": {
                "id": 24911051,
                "name": "Saya",
                "participants": [{"gamerTag": "Saya", "prefix": None, "user": None}],
            },
            "standing": {"stats": {"score": {"value": 0}}},
        },
    ],
}
STARTGG_SET_TBD = {
    **STARTGG_SET,
    "id": 110477945,
    "startedAt": None,
    "completedAt": None,
    "winnerId": None,
    "games": None,
    "slots": [{"entrant": None, "standing": None}, {"entrant": None, "standing": None}],
}
