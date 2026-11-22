import pytest

from app.config import Settings
from app.routers import internal


@pytest.fixture
def secret(monkeypatch):
    monkeypatch.setattr(internal, "get_settings", lambda: Settings(sync_secret="s3cret"))
    calls = []

    def fake_run_sync():
        calls.append(1)
        internal._running.release()

    monkeypatch.setattr(internal, "run_sync", fake_run_sync)
    return calls


def test_sync_route_is_hidden_without_a_secret(client, monkeypatch):
    monkeypatch.setattr(internal, "get_settings", lambda: Settings(sync_secret=""))
    assert client.post("/internal/sync").status_code == 404


def test_sync_route_rejects_a_wrong_secret(client, secret):
    r = client.post("/internal/sync", headers={"X-Sync-Secret": "nope"})
    assert r.status_code == 403
    assert secret == []


def test_sync_route_starts_one_cycle(client, secret):
    r = client.post("/internal/sync", headers={"X-Sync-Secret": "s3cret"})
    assert (r.status_code, r.json()) == (202, {"status": "started"})
    assert secret == [1]


def test_sync_route_skips_when_a_cycle_is_running(client, secret):
    internal._running.acquire()
    try:
        r = client.post("/internal/sync", headers={"X-Sync-Secret": "s3cret"})
        assert r.json() == {"status": "already running"}
        assert secret == []
    finally:
        internal._running.release()


@pytest.mark.parametrize(
    "url",
    [
        "postgres://u:p@h:5432/db",
        "postgresql://u:p@h:5432/db",
        "postgresql+psycopg://u:p@h:5432/db",
    ],
)
def test_database_url_uses_psycopg(url):
    assert Settings(database_url=url).database_url == "postgresql+psycopg://u:p@h:5432/db"
