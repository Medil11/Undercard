"""Thin HTTP client for the PandaScore REST API (https://developers.pandascore.co)."""

import httpx

STATUSES = ("running", "upcoming", "past")
MAX_PAGE_SIZE = 100


class PandaScoreClient:
    def __init__(
        self,
        token: str,
        base_url: str = "https://api.pandascore.co",
        timeout: float = 15.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._http = httpx.Client(
            base_url=base_url,
            headers={"Authorization": f"Bearer {token}"},
            timeout=timeout,
            transport=transport,
        )

    def matches(
        self, status: str, per_page: int = 50, videogame: str | None = None, page: int = 1
    ) -> list[dict]:
        if status not in STATUSES:
            raise ValueError(f"status must be one of {STATUSES}")
        params: dict[str, str | int] = {
            "per_page": per_page,
            # begin_at is null until a match starts and nulls sort first, so use scheduled_at.
            "sort": "-scheduled_at" if status == "past" else "scheduled_at",
            "page": page,
        }
        if videogame:
            params["filter[videogame]"] = videogame
        response = self._http.get(f"/matches/{status}", params=params)
        response.raise_for_status()
        return response.json()

    def matches_by_ids(self, ids: list[int]) -> list[dict]:
        """Fetch up to 100 matches by id, whatever their status, in a single request."""
        if not 0 < len(ids) <= MAX_PAGE_SIZE:
            raise ValueError(f"pass between 1 and {MAX_PAGE_SIZE} match ids")
        params = {"filter[id]": ",".join(map(str, ids)), "per_page": MAX_PAGE_SIZE}
        response = self._http.get("/matches", params=params)
        response.raise_for_status()
        return response.json()

    def teams(self, ids: list[int]) -> list[dict]:
        """Fetch up to 100 teams (with their current players) in a single request."""
        if not 0 < len(ids) <= MAX_PAGE_SIZE:
            raise ValueError(f"pass between 1 and {MAX_PAGE_SIZE} team ids")
        params = {"filter[id]": ",".join(map(str, ids)), "per_page": MAX_PAGE_SIZE}
        response = self._http.get("/teams", params=params)
        response.raise_for_status()
        return response.json()

    def standings(self, tournament_id: int) -> list[dict]:
        """Rank, team and last match of every team in a tournament."""
        response = self._http.get(f"/tournaments/{tournament_id}/standings")
        response.raise_for_status()
        return response.json()

    def brackets(self, tournament_id: int) -> list[dict]:
        """Every match of a tournament, with previous_matches: the links of the playoff tree."""
        response = self._http.get(f"/tournaments/{tournament_id}/brackets")
        response.raise_for_status()
        return response.json()

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> "PandaScoreClient":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()
