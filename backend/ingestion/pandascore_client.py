"""Thin HTTP client for the PandaScore REST API (https://developers.pandascore.co)."""

import httpx

STATUSES = ("running", "upcoming", "past")


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

    def matches(self, status: str, per_page: int = 50, videogame: str | None = None) -> list[dict]:
        if status not in STATUSES:
            raise ValueError(f"status must be one of {STATUSES}")
        params: dict[str, str | int] = {
            "per_page": per_page,
            "sort": "-begin_at" if status == "past" else "begin_at",
        }
        if videogame:
            params["filter[videogame]"] = videogame
        response = self._http.get(f"/matches/{status}", params=params)
        response.raise_for_status()
        return response.json()

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> "PandaScoreClient":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()
