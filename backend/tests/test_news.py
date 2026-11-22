from app.routers import news

FEED = """<?xml version="1.0"?>
<rss xmlns:media="http://search.yahoo.com/mrss/"><channel>
<item><title>Tekken upset</title><link>https://www.dexerto.com/tekken/upset-1/</link>
  <pubDate>Sat, 14 Nov 2026 21:03:52 GMT</pubDate><description>Kid wins.</description>
  <enclosure url="https://img.example/t.jpg" type="image/jpeg"/></item>
<item><title>Major news</title><link>https://www.dexerto.com/entertainment/x/</link>
  <pubDate>Sun, 15 Nov 2026 10:00:00 GMT</pubDate></item>
<item><title>Bad link</title><link>javascript:alert(1)</link></item>
</channel></rss>"""


def test_parse_feed_reads_items_and_guesses_the_game():
    items = news.parse_feed(FEED, "Dexerto", None)
    assert [i["title"] for i in items] == ["Tekken upset", "Major news"]  # unsafe link dropped
    assert items[0]["game"] == "tekken-8" and items[1]["game"] is None
    assert items[0]["image_url"] == "https://img.example/t.jpg"
    assert items[0]["published_at"].year == 2026


def test_news_route_sorts_and_caches(client, monkeypatch):
    calls = []

    def fake(url):
        calls.append(url)
        return news.parse_feed(FEED, "Dexerto", None) if "esports" in url else []

    monkeypatch.setattr(news, "_fetch", fake)
    monkeypatch.setattr(news, "_cache", {"at": 0.0, "items": []})
    body = client.get("/news").json()
    assert [i["title"] for i in body] == ["Major news", "Tekken upset"]  # newest first
    client.get("/news")
    assert len(calls) == len(news.FEEDS)  # second call served from the cache
