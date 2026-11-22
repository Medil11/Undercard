"""Esports headlines from free RSS feeds (no account), cached in memory."""

import logging
import time
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["news"])
log = logging.getLogger("api")

# feed url -> (source name, game slug or None when the feed covers every game)
FEEDS = {
    "https://www.hltv.org/rss/news": ("HLTV", "cs-go"),
    "https://www.dexerto.com/esports/feed/": ("Dexerto", None),
    "https://www.dexerto.com/league-of-legends/feed/": ("Dexerto", "league-of-legends"),
    "https://www.dexerto.com/valorant/feed/": ("Dexerto", "valorant"),
}
# Dexerto puts the game in the first path segment: dexerto.com/tekken/...
PATH_GAMES = {
    "league-of-legends": "league-of-legends",
    "valorant": "valorant",
    "counter-strike": "cs-go",
    "dota-2": "dota-2",
    "overwatch": "ow",
    "rocket-league": "rl",
    "call-of-duty": "cod-mw",
    "rainbow-six": "r6-siege",
    "mobile-legends": "mlbb",
    "street-fighter": "sf6",
    "tekken": "tekken-8",
    "super-smash-bros": "ssbu",
    "mortal-kombat": "mk1",
}
TTL = 900  # seconds
MAX_ITEMS = 80
MEDIA = "{http://search.yahoo.com/mrss/}"
_cache: dict = {"at": 0.0, "items": []}


class NewsOut(BaseModel):
    title: str
    url: str
    source: str
    published_at: datetime | None = None
    image_url: str | None = None
    game: str | None = None
    summary: str | None = None


def _http_url(value: str | None) -> str | None:
    return value if value and urlparse(value).scheme in ("http", "https") else None


def parse_feed(xml: str, source: str, game: str | None) -> list[dict]:
    items = []
    for item in ET.fromstring(xml).iter("item"):
        url = _http_url((item.findtext("link") or "").strip())
        title = (item.findtext("title") or "").strip()
        if not url or not title:
            continue
        image = next(
            (
                el.get("url")
                for el in (
                    item.find(f"{MEDIA}content"),
                    item.find("enclosure"),
                    item.find(f"{MEDIA}thumbnail"),
                )
                if el is not None and el.get("url")
            ),
            None,
        )
        try:
            published = parsedate_to_datetime(item.findtext("pubDate") or "").astimezone(UTC)
        except (TypeError, ValueError):
            published = None
        segment = urlparse(url).path.strip("/").split("/")[0]
        items.append(
            {
                "title": title,
                "url": url,
                "source": source,
                "published_at": published,
                "image_url": _http_url(image),
                "game": game or PATH_GAMES.get(segment),
                "summary": (item.findtext("description") or "").strip()[:300] or None,
            }
        )
    return items


def _fetch(url: str) -> list[dict]:
    source, game = FEEDS[url]
    try:
        response = httpx.get(
            url, timeout=10, follow_redirects=True, headers={"User-Agent": "Undercard/1.0"}
        )
        response.raise_for_status()
        return parse_feed(response.text, source, game)
    except Exception:
        log.exception("news feed failed: %s", url)
        return []


@router.get("/news", response_model=list[NewsOut])
def list_news() -> list[dict]:
    """Latest headlines from every feed, newest first, deduplicated by url."""
    if _cache["items"] and time.monotonic() - _cache["at"] < TTL:
        return _cache["items"]
    with ThreadPoolExecutor(len(FEEDS)) as pool:
        fetched = [i for items in pool.map(_fetch, FEEDS) for i in items]
    if not fetched:
        return _cache["items"]  # every feed failed: keep the old headlines
    unique = {}
    for item in fetched:  # a game feed wins over the general one, it carries the game
        if item["url"] not in unique or item["game"]:
            unique[item["url"]] = item
    oldest = datetime.min.replace(tzinfo=UTC)
    items = sorted(unique.values(), key=lambda i: i["published_at"] or oldest, reverse=True)
    _cache.update(at=time.monotonic(), items=items[:MAX_ITEMS])
    return _cache["items"]
